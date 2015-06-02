import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../')
)
sys.path.append(PROJECT_HOME)
import unittest
from flask.ext.testing import TestCase
from app import create_app
from models import db, FavoriteColor

class TestDatabase(TestCase):
    """
    Test flask-sqlalchemy database operations
    """
    def create_app(self):
        """
        Called once at the beginning of the tests; must return the application
        instance
        :return: flask.Flask application instance
        """
        _app = create_app()
        # Override whatever database uri is in the config for tests;
        # Use an in-memory sqlite database to ensure that no production data
        # are touched
        _app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"
        return _app

    def setUp(self):
        """
        setUp and tearDown are run at the start of each test; ensure
        that a fresh database is used for each test.
        """
        db.create_all()

    def tearDown(self):
        """
        setUp and tearDown are run at the start of each test; ensure
        that a fresh database is used for each test.
        """
        db.session.remove()
        db.drop_all()

if __name__ == '__main__':
    unittest.main(verbosity=2)
