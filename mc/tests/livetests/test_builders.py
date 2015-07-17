"""
Test builders
"""
import unittest
from mc.builders import DockerRunner
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
        print self.builder.client.containers(
            filters={'status': 'running'}
        )
        running = [i['Names'][0] for i in self.builder.client.containers(
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