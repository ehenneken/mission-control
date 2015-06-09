"""
Example manage.py script, which is responsible for providing a command-line
interface to application specific tasks, such as managing databases.
"""
import os, sys
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(PROJECT_HOME)

from flask.ext.script import Manager, Command
from flask.ext.migrate import Migrate, MigrateCommand
from mc.models import db
from mc.app import create_app

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


manager.add_command('db', MigrateCommand)
manager.add_command('createdb', CreateDatabase())

if __name__ == '__main__':
    manager.run()
