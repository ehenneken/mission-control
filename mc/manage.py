"""
Example manage.py script, which is responsible for providing a command-line
interface to application specific tasks, such as managing databases.
"""
import os
import sys
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_HOME)
from dateutil import parser
import requests
from flask.ext.script import Manager, Command, Option
from flask.ext.migrate import Migrate, MigrateCommand
from flask import current_app
from mc.models import db, Build, Commit
from mc.app import create_app
from mc.tasks import build_docker, register_task_revision
from mc.builders import ECSBuilder
from sqlalchemy.orm.exc import NoResultFound

app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)


class CreateDatabase(Command):
    """
    Creates the database based on models.py
    """

    def run(self):
        with app.app_context():
            db.create_all()


class BuildDockerImage(Command):
    """
    Generates a build based on a repo name and commit hash
    """
    option_list = (
        Option('--repo', '-r', dest='repo'),
        Option('--commit', '-c', dest='commit_hash')
    )

    def run(self, repo, commit_hash, app=app):
        with app.app_context():
            url = current_app.config['GITHUB_COMMIT_API'].format(
                repo=repo,
                hash=commit_hash
            )
            r = requests.get(url)
            r.raise_for_status()
            payload = r.json()
            try:
                c = Commit.query.filter_by(
                    commit_hash=commit_hash,
                    repository=repo
                ).one()
            except NoResultFound:
                c = Commit(
                    commit_hash=commit_hash,
                    timestamp=parser.parse(payload['author']['date']),
                    author=payload['author']['name'],
                    repository=repo,
                    message=payload['message'],
                )
            db.session.add(c)
            db.session.commit()
            build_docker.delay(c.id)
            current_app.logger.info(
                "user-received: {}@{}".format(c.repository, c.commit_hash)
            )


class MakeDockerrunTemplate(Command):
    """
    Prints a `Dockerrun.aws.json` to stdout
    Usage: manage.py render_dockerrun -c adsws:2cfd... staging 100 -c biblib:j03b... staging 300
    """

    option_list = (
        Option(
            '--containers',
            '-c',
            dest='containers',
            nargs=3,
            action='append'
        ),
        Option(
            '--family',
            '-f',
            dest='family',
            nargs=1,
        )
    )

    def run(self, containers, family, app=app):
        apps = []
        with app.app_context():
            for container in containers:
                try:
                    repo, commit_hash = container[0].split(':')
                except ValueError:
                    raise ValueError(
                        '"{}" should look like repo:id'.format(container[0])
                    )
                build = Build.query.join(Commit).filter(
                    Commit.repository == repo,
                    Commit.commit_hash == commit_hash,
                ).first()
                if build is None:
                    raise NoResultFound("No row found for {}/{}".format(
                        repo, commit_hash)
                    )
                apps.append(ECSBuilder.DockerContainer(
                    build, container[1], container[2])
                )
            tmpl = ECSBuilder(apps, family=family).render_template()
            print(tmpl)
            return tmpl


class ECSDeploy(Command):
    """
    Calls tasks.register_task_definition (TODO: and update_service) to update
    an AWS deploy
    """

    option_list = (
        Option('--task', '-t', dest='task_definition'),
    )

    def run(self, task_definition, app=app):
        with app.app_context():
            register_task_revision(task_definition)

manager.add_command('deploy', ECSDeploy)
manager.add_command('db', MigrateCommand)
manager.add_command('createdb', CreateDatabase())
manager.add_command('dockerbuild', BuildDockerImage)
manager.add_command('render_dockerrun', MakeDockerrunTemplate)


if __name__ == '__main__':
    manager.run()
