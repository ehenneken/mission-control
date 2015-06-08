"""
Test utilities
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest
from flask.ext.testing import TestCase
from mock import patch
from mc import app
from mc import tasks
from mc.models import db, Commit, Build
import datetime


class TestDockerBuildTask(TestCase):
    """
    Test the Build task
    """
    def create_app(self):
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app_.config['MC_LOGGING'] = {}
        return app_

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

    @patch('mc.builders.DockerBuilder.run', lambda l: None)
    def test_docker_build_task(self):
        """
        Tests that the docker_build_task adds a Build entry. Assumes the
        underlying builder.run command does not Raise
        """
        commit = Commit(
            repository='test-repo',
            commit_hash='test-hash',
        )
        db.session.add(commit)
        tasks.build_docker(commit)

        build = db.session.query(Build).first()
        self.assertEqual(build.commit_id, commit.id)
        self.assertAlmostEqual(
            build.timestamp,
            datetime.datetime.now(),
            delta=datetime.timedelta(seconds=1)
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)