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

    @patch('mc.builders.Client')
    def test_docker_build_task(self, mocked):
        """
        Tests that the docker_build_task adds a Build entry. Assumes the
        underlying builder.run command does not Raise
        """
        commit = Commit(
            repository='adsws',
            commit_hash='test-hash',
        )
        db.session.add(commit)
        db.session.commit()
        commit_id = commit.id

        instance = mocked.return_value
        instance.build.return_value = ['Successfully built']
        instance.push.return_value = ['pushing tag']

        tasks.build_docker(commit_id)

        build = db.session.query(Build).first()
        self.assertEqual(build.commit_id, commit_id)
        self.assertAlmostEqual(
            build.timestamp,
            datetime.datetime.now(),
            delta=datetime.timedelta(seconds=1)
        )
        self.assertTrue(build.built)
        self.assertTrue(build.pushed)


if __name__ == '__main__':
    unittest.main(verbosity=2)