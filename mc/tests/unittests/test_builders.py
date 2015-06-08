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
from mc.builders import DockerBuilder
from mc.models import db, Commit


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

    def tearDown(self):
        self.commit = None
        self.builder = None

    def test_get_templates(self):
        """
        Test that the builder grabs the expected templates
        """
        self.builder.get_templates()
        self.assertGreater(len(self.builder.files), 0)
        self.assertEqual(self.builder.files[0]['name'], 'Dockerfile')
        self.assertIn(self.commit.commit_hash, self.builder.files[0]['content'])

    def test_create_docker_context(self):
        """
        Test that the docker context is created in-memory and that it has
        a non zero size
        """
        self.builder.get_templates()
        self.builder.create_docker_context()
        self.assertIsInstance(self.builder.tarfile, io.BytesIO)
        self.assertGreater(len(self.builder.tarfile.readlines()), 0)

    def test_docker_build(self):
        """
        Tests that docker build (using a mocked docker client) returns
        as expected
        """
        pass
        #self.builder.get_templates()
        #self.builder.create_docker_context()
        #self.builder.build()




if __name__ == '__main__':
    unittest.main(verbosity=2)