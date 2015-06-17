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
from mc.builders import DockerImageBuilder, DockerRunner
from mc.models import Commit
from werkzeug.security import gen_salt


class TestDockerRunner(unittest.TestCase):
    """
    Test the docker runner
    """

    def setUp(self):
        self.name = 'livetest-redis-{}'.format(gen_salt(5))
        self.builder = DockerRunner(
            image='redis',
            name=self.name,
            mem_limit="50m",
        )

    def tearDown(self):
        """
        the teardown() method should result in the container being stopped and
        removed
        """
        self.builder.teardown()

        running = [i['Name'] for i in self.builder.client.containers(
            filters={'status': 'running'}
        )]
        self.assertNotIn(self.name, running)
        self.assertNotIn(
            {'Id': self.builder.container['Id']},
            self.builder.client.containers(quiet=True, all=True)
        )

    def test_initialization(self):
        """
        the Dockerrunner.setup() method should modify its container
        attribute, that container should exist in `docker ps -a`
        """
        self.assertIn('Id', self.builder.container)
        self.assertIn(
            {'Id': self.builder.container['Id']},
            self.builder.client.containers(quiet=True, all=True)
        )

    def test_start(self):
        """
        the start() method should run an option callback after calling
        docker.Client.start with the expected container id
        The container should be listed in `docker ps`
        """
        def cb(container):
            self.assertEqual(container['Id'], self.builder.container['Id'])
        self.builder.start(callback=cb)

        running = [i['Id'] for i in self.builder.client.containers(
            filters={'status': 'running'}
        )]
        self.assertIn(self.builder.container['Id'], running)




if __name__ == '__main__':
    unittest.main(verbosity=2)