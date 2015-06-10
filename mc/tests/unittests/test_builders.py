"""
Test builders
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest
import io
import mock
from mc.builders import DockerBuilder
from mc.models import Commit


class TestDockerBuilder(unittest.TestCase):
    """
    Test the DockerBuilder
    """

    def setUp(self):
        self.commit = Commit(
            commit_hash='master',
            repository="adsws"
        )
        self.builder = DockerBuilder(self.commit)

    def test_get_templates(self):
        """
        Test that the builder grabs the expected templates.
        This uses "live" templates.
        """
        self.builder.get_templates()
        self.assertGreater(len(self.builder.files), 0)
        self.assertEqual(self.builder.files[0]['name'], 'Dockerfile')
        self.assertIn(self.commit.commit_hash, self.builder.files[0]['content'])

    def test_create_docker_context(self):
        """
        Test that the docker context is created in-memory and that it has
        a non zero size. This uses "live" templates.
        """
        self.builder.get_templates()
        self.builder.create_docker_context()
        self.assertIsInstance(self.builder.tarfile, io.BytesIO)
        self.assertGreater(len(self.builder.tarfile.readlines()), 0)

    @mock.patch('mc.builders.Client')
    def test_docker_build(self, mocked):
        """
        Tests that docker build (using a mocked docker client) returns
        as expected
        """
        instance = mocked.return_value
        instance.build.return_value = ['Successfully built']
        self.builder.build()
        self.assertTrue(self.builder.built)

    @mock.patch('mc.builders.Client')
    def test_docker_push(self, mocked):
        """
        Tests that docker push (using a mocked docker client) returns
        as expected
        """
        instance = mocked.return_value
        instance.push.return_value = ['pushing tag']
        self.builder.push()
        self.assertTrue(self.builder.pushed)




if __name__ == '__main__':
    unittest.main(verbosity=2)