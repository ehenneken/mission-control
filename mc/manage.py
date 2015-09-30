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
from mc.tasks import build_docker, register_task_revision, update_service, \
    start_test_environment, stop_test_environment
from mc.builders import ECSBuilder
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound

app = create_app()
migrate = Migrate(app, db)
manager = Manager(app)


class ManageTestCluster(Command):
    """
    Script to allow the management of the test cluster
    """
    option_list = (
        Option('--command', '-c', dest='command', choices=['start', 'stop'])
    )

    def run(self, command):
        """
        Run command
        :param command: command to pass to the cluster environment
        """

        command_look_up = {
            'start': start_test_environment,
            'stop': stop_test_environment,
        }
        command_look_up[command]()


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
        Option('--commit', '-c', dest='commit_hash'),
        Option('--tag', '-t', dest='tag')
    )

    def run(self, repo, commit_hash=None, tag=None, app=app):
        with app.app_context():

            if tag:
                # Using the tag, obtain the sha for the relevant tag
                url = current_app.config['GITHUB_TAG_FIND_API'].format(
                    repo=repo,
                    tag=tag
                )
                r = requests.get(url)
                r.raise_for_status()
                payload_find_tag = r.json()
                try:
                    tag_commit_hash = payload_find_tag['object']['sha']
                except KeyError:
                    raise KeyError(
                        'tag supplied does not exist: {0}'.format(tag)
                    )

                # Obtain the commit hash for this tag
                url = current_app.config['GITHUB_TAG_GET_API'].format(
                    repo=repo,
                    hash=tag_commit_hash
                )
                r = requests.get(url)
                r.raise_for_status()
                payload_get_tag = r.json()
                commit_hash = payload_get_tag['object']['sha']

                current_app.logger.info(
                    'user supplied a tag: {0}, sha: {1}'
                    .format(tag, commit_hash)
                )

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

                if not c.tag and tag:
                    c.tag = tag

            except NoResultFound:
                c = Commit(
                    commit_hash=commit_hash,
                    timestamp=parser.parse(payload['author']['date']),
                    author=payload['author']['name'],
                    repository=repo,
                    message=payload['message'],
                    tag=tag if tag else None
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
    Usage: manage.py print_task_def -c adsws:2cfd... staging 100 -c biblib:j03b... staging 300
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
                    or_(Commit.commit_hash == commit_hash, Commit.tag == commit_hash),
                ).first()
                if build is None:
                    raise NoResultFound("No row found for {}/{}".format(
                        repo, commit_hash)
                    )
                apps.append(ECSBuilder.DockerContainer(
                    build=build,
                    environment=container[1],
                    memory=container[2],
                    portmappings=[
                        {"hostPort": 8080, "containerPort": 80}
                    ] if repo == "adsws" else None,
                    )
                )
            tmpl = ECSBuilder(apps, family=family).render_template()
            print(tmpl)
            return tmpl


class RegisterTaskRevision(Command):
    """
    Calls tasks.register_task_definition to update
    an ECS task revision
    """

    option_list = (
        Option('--task', '-t', dest='task_definition'),
    )

    def run(self, task_definition, app=app):
        with app.app_context():
            register_task_revision(task_definition)


class UpdateService(Command):
    """
    Calls tasks.update_service to update an ECS service
    """

    option_list = (
        Option('--cluster', '-c', dest='cluster'),
        Option('--service', '-s', dest='service'),
        Option('--desiredCount', dest='desiredCount', type=int),
        Option('--taskDefinition', '-t', dest='taskDefinition'),
    )

    def run(self, cluster, service, desiredCount, taskDefinition, app=app):
        with app.app_context():
            update_service(cluster=cluster,
                           service=service,
                           desiredCount=desiredCount,
                           taskDefinition=taskDefinition,
                           )


manager.add_command('update_service', UpdateService)
manager.add_command('register_task_def', RegisterTaskRevision)
manager.add_command('db', MigrateCommand)
manager.add_command('createdb', CreateDatabase())
manager.add_command('dockerbuild', BuildDockerImage)
manager.add_command('print_task_def', MakeDockerrunTemplate)


if __name__ == '__main__':
    manager.run()
