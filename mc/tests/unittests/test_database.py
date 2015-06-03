import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../')
)
sys.path.append(PROJECT_HOME)
import unittest
from flask.ext.testing import TestCase
from mc.app import create_app
from mc.models import db, Commit, Build

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
        _app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
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

    def test_commits(self):
        """
        CRUD on Commits
        """

        # Create
        commit = Commit(commit_hash='test-hash')
        db.session.add(commit)
        db.session.commit()

        # Read
        c = Commit.query.first()
        self.assertEqual(c, commit)

        # Update
        c.commit_hash = 'mutated'
        db.session.commit()
        self.assertEqual(Commit.query.first().commit_hash, 'mutated')

        # Delete
        c = Commit.query.first()
        db.session.delete(c)
        db.session.commit()
        self.assertIsNone(Commit.query.first())

if __name__ == '__main__':
    unittest.main(verbosity=2)

