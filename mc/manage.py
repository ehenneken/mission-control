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
from mc.models import db
from mc.app import create_app
from mc.tasks import build_docker
from mc.models import Commit


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


class Build(Command):
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


manager.add_command('db', MigrateCommand)
manager.add_command('createdb', CreateDatabase())

if __name__ == '__main__':
    manager.run()
