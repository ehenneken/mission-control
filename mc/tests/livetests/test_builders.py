"""
Test builders
"""
import time
import unittest

from mc import config
from mc.builders import DockerRunner, ConsulDockerRunner, PostgresDockerRunner, \
    RedisDockerRunner, GunicornDockerRunner, RegistratorDockerRunner, SolrDockerRunner
from werkzeug.security import gen_salt


class TestDockerRunner(unittest.TestCase):
    """
    Test the docker runner
    """

    def setUp(self):
        self.name = 'livetest-redis-{}'.format(gen_salt(5))
        self.builder = DockerRunner(
            image=config.DEPENDENCIES['REDIS']['IMAGE'],
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


class TestBaseDockerRunner(unittest.TestCase):

    def setUp(self):
        self.name = 'livetest-service-{}'.format(gen_salt(5))
        self.builder = DockerRunner(
            name=self.name,
        )

    def tearDown(self):
        """
        teardown the containers
        """
        try:
            self.builder.teardown()
        except:
            pass

    def helper_is_service_ready(self):
        """
        Check if the instance is ready
        """

        self.builder.start()

        self.assertTrue(self.builder.running)
        self.assertTrue(self.builder.ready)

        self.builder.teardown()
        self.assertFalse(self.builder.ready)
        self.assertFalse(self.builder.running)


class TestRedisDockerRunner(unittest.TestCase):
    """
    Test the docker runner for the Redis cache
    """

    def setUp(self):
        self.name = 'livetest-redis-{}'.format(gen_salt(5))
        self.builder = RedisDockerRunner(
            name=self.name,
        )

    def tearDown(self):
        """
        teardown the containers
        """
        try:
            self.builder.teardown()
        except:
            pass

    def test_is_ready(self):
        """
        Check if the instance is ready
        """

        self.builder.start()
        while not self.builder.ready:
            time.sleep(1)
        self.assertTrue(self.builder.running)
        self.assertTrue(self.builder.ready)

        self.builder.teardown()
        self.assertFalse(self.builder.ready)
        self.assertFalse(self.builder.running)


class TestConsulDockerRunner(unittest.TestCase):
    """
    Test the docker runner for the Consul service
    """

    def setUp(self):
        self.name = 'livetest-consul-{}'.format(gen_salt(5))
        self.builder = ConsulDockerRunner(
            name=self.name,
        )

    def tearDown(self):
        """
        teardown the containers
        """
        try:
            self.builder.teardown()
        except:
            pass

    def test_is_ready(self):
        """
        Check if the instance is ready
        """

        self.builder.start()
        while not self.builder.ready:
            time.sleep(1)
        self.assertTrue(self.builder.running)
        self.assertTrue(self.builder.ready)

        self.builder.teardown()
        self.assertFalse(self.builder.ready)
        self.assertFalse(self.builder.running)


class TestPostgresDockerRunner(unittest.TestCase):
    """
    Test the docker runner for the Postgres service
    """

    def setUp(self):
        self.name = 'livetest-postgres-{}'.format(gen_salt(5))
        self.builder = PostgresDockerRunner(
            name=self.name,
        )

    def tearDown(self):
        """
        teardown the containers
        """
        try:
            self.builder.teardown()
        except:
            pass

    def test_is_ready(self):
        """
        Check if the instance is ready
        """

        self.builder.start()

        self.assertTrue(self.builder.running)
        self.assertTrue(self.builder.ready)

        self.builder.teardown()
        self.assertFalse(self.builder.ready)
        self.assertFalse(self.builder.running)


class TestGunicornDockerRunner(unittest.TestCase):
    """
    Test the docker runner for the Postgres service
    """

    def setUp(self):
        self.name = 'livetest-gunicorn-{}'.format(gen_salt(5))
        self.builder = GunicornDockerRunner(
            image='adsabs/pythonsimpleserver:v1.0.0',
            name=self.name,
        )

    def tearDown(self):
        """
        teardown the containers
        """
        try:
            self.builder.teardown()
        except:
            pass

    def test_is_ready(self):
        """
        Check if the instance is ready
        """

        self.builder.start()

        self.assertTrue(self.builder.running)
        self.assertTrue(self.builder.ready)

        self.builder.teardown()
        self.assertFalse(self.builder.ready)
        self.assertFalse(self.builder.running)


class TestRegistratorDockerRunner(TestBaseDockerRunner):
    """
    Test the docker runner for the Registrator service
    """

    def setUp(self):
        self.name = 'livetest-registrator-{}'.format(gen_salt(5))
        self.builder = RegistratorDockerRunner(
            image='gliderlabs/registrator:latest',
            name=self.name,
        )

    def tearDown(self):
        """
        teardown the containers
        """
        try:
            self.builder.teardown()
        except:
            pass

    def test_is_ready(self):
        """
        Check if the instance is ready
        """
        self.helper_is_service_ready()


class TestSolrDockerRunner(TestBaseDockerRunner):
    """
    Test the docker runner for the Solr service
    """

    def setUp(self):
        self.name = 'livetest-solr-{}'.format(gen_salt(5))
        self.builder = SolrDockerRunner(
            name=self.name,
        )

    def test_is_ready(self):
        """
        Check if the instance is ready
        """
        self.helper_is_service_ready()

