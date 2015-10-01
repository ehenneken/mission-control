"""
Test builders
"""

import re
import io
import mock
import jinja2
import json
import tarfile
import unittest
import httpretty
import requests

from sqlalchemy.exc import OperationalError
from mc.builders import DockerImageBuilder, DockerRunner, ECSBuilder, ConsulDockerRunner, PostgresDockerRunner
from mc.models import Commit, Build
from mc.exceptions import BuildError
from httmock import all_requests, HTTMock


@all_requests
def response_500(url, request):
    return {'status_code': 500, 'content': 'Failed'}

@all_requests
def response_404(url, request):
    return {'status_code': 404, 'content': 'Not found'}

class TestECSbuilder(unittest.TestCase):
    """
    Test the ECSBuilder
    """
    def setUp(self):
        self.commit = Commit(
            commit_hash='master',
            repository="adsws"
        )
        self.build = Build(commit=self.commit)
        self.containers = [
            ECSBuilder.DockerContainer(
                self.build,
                environment="staging",
                memory=m,
                portmappings=[{
                    "hostPort": 8080,
                    "containerPort": 80}] if m == 10 else None
            ) for m in range(10, 50, 10)
        ]
        self.builder = ECSBuilder(self.containers, family="unittest")

    def test_init(self):
        """
        Initialized ECSBuilder should have a template and containers attribute
        of the appropriate types
        """
        self.assertIsInstance(
            self.builder.containers[0],
            ECSBuilder.DockerContainer
        )
        self.assertEqual(self.builder.containers, self.containers)
        self.assertIsInstance(
            self.builder.templates,
            jinja2.environment.Environment
        )

    def test_render_template(self):
        """
        instance method render_template should return a json template based
        on base.aws.template
        """
        t = self.builder.render_template()
        self.assertIsInstance(t, basestring)
        try:
            j = json.loads(t)
        except ValueError:
            print("Could not load json: {}".format(t))
            raise
        self.assertIn(self.commit.repository, t)
        for container in self.containers:
            self.assertIn("{}".format(container.memory), t)
            if container.portmappings is not None:
                self.assertEqual(
                    j['containerDefinitions'][self.containers.index(container)]['portMappings'],
                    container.portmappings,
                )


class TestDockerImageBuilder(unittest.TestCase):
    """
    Test the DockerImageBuilder
    """
    def setUp(self):
        self.commit = Commit(
            commit_hash='master',
            repository="adsws"
        )
        self.builder = DockerImageBuilder(self.commit)

    def test_get_templates(self):
        """
        Test that the builder grabs the expected templates.
        This uses "live" templates.
        """
        self.builder.render_templates()
        self.assertGreater(len(self.builder.files), 0)
        self.assertEqual(self.builder.files[0]['name'], 'Dockerfile')
        self.assertIn(self.commit.commit_hash, self.builder.files[0]['content'])

    def test_create_docker_context(self):
        """
        Test that the docker context is created in-memory and that it has
        a non zero size. This uses "live" templates.
        """
        self.builder.render_templates()
        self.builder.create_docker_context()
        self.assertIsInstance(self.builder.tarfile, io.BytesIO)
        with tarfile.open(fileobj=self.builder.tarfile) as tf:
            for fn in ["Dockerfile", "gunicorn.conf.py", "app.nginx.conf"]:
                f = tf.getmember(fn)
                self.assertEqual(f.mode, 420)
            for fn in ["gunicorn.sh", "nginx.sh"]:
                f = tf.getmember(fn)
                self.assertEqual(f.mode, 0555)

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

        self.builder.pushed = False
        instance.push.return_value = ['DIGEST: sha256']
        self.builder.push()
        self.assertTrue(self.builder.pushed)

        instance.push.return_value = ['error']
        with self.assertRaises(BuildError):
            self.builder.push()


class TestDockerRunner(unittest.TestCase):
    """
    Test the docker runner
    """

    @mock.patch('mc.builders.Client')
    def setUp(self, mocked):
        instance = mocked.return_value
        instance.create_container.return_value = {'Id': 'mocked'}
        instance.containers.return_value = [
            {
                u'Command': u'/entrypoint.sh redis-server',
                u'Created': 1443632967,
                u'Id': u'mocked',
                u'Image': u'redis',
                u'Labels': {},
                u'Names': [u'/livetest-redis-tLJpZ'],
                u'Ports': [{u'PrivatePort': 6379, u'Type': u'tcp'}],
                u'Status': u'Up About a minute'
            }
        ]
        self.instance = instance
        self.builder = DockerRunner(
            image='redis',
            name='redis',
            mem_limit="100m",
            network_mode="host"
        )

    def test_initialization(self):
        """
        the Dockerrunner.setup() method should modify its container
        attribute, and client.create_container should be called with the
        expected kwargs
        """
        self.assertEqual(self.builder.container,  {'Id': 'mocked'})
        self.instance.create_container.assert_called_with(
            host_config={'NetworkMode': 'host', "Memory": 104857600},
            name='redis',
            image='redis',
            command=None
        )
        self.instance.pull.assert_called_with('redis')

    def test_start(self):
        """
        the start() method should run an option callback after calling
        docker.Client.start with the expected container id
        """
        def cb(container):
            self.assertEqual(container, {'Id': 'mocked'})
        self.builder.start(callback=cb)
        self.instance.start.assert_called_with(container='mocked')

    def test_teardown(self):
        """
        the teardown() method should be called with the correct container id
        """
        self.builder.time_out = 0.1
        self.builder.teardown()
        self.instance.stop.assert_called_with(container='mocked')
        self.instance.remove_container.assert_called_with(container='mocked')

    def test_running(self):
        """
        Tests if the docker container is running
        """

        self.instance.containers.return_value = []
        self.assertFalse(self.builder.running)

        self.instance.containers.return_value = [
            {
                u'Command': u'/entrypoint.sh redis-server',
                u'Created': 1443632967,
                u'Id': u'mocked',
                u'Image': u'redis',
                u'Labels': {},
                u'Names': [u'/livetest-redis-tLJpZ'],
                u'Ports': [{u'PrivatePort': 6379, u'Type': u'tcp'}],
                u'Status': u'Up About a minute'
            }
        ]
        self.assertTrue(self.builder.running)


class TestConsulDockerRunner(unittest.TestCase):
    """
    Test the docker runner
    """

    @mock.patch('mc.builders.Client')
    def setUp(self, mocked):
        instance = mocked.return_value
        instance.create_container.return_value = {'Id': 'mocked'}
        instance.port.return_value = [{'HostIp': '127.0.0.1', 'HostPort': 1234}]
        instance.containers.return_value = [
            {
                u'Command': u'/entrypoint.sh redis-server',
                u'Created': 1443632967,
                u'Id': u'mocked',
                u'Image': u'redis',
                u'Labels': {},
                u'Names': [u'/livetest-redis-tLJpZ'],
                u'Ports': [{u'PrivatePort': 6379, u'Type': u'tcp'}],
                u'Status': u'Up About a minute'
            }
        ]
        self.instance = instance
        self.builder = ConsulDockerRunner(network_mode="host")

    def test_ready(self):
        """
        Tests the health check of the service and makes sure it is ready
        """
        with HTTMock(response_404):
            self.assertTrue(self.builder.ready)

    def test_not_ready(self):
        """
        Tests the health check of the service and makes sure it is not ready
        """
        with HTTMock(response_500):
            self.assertFalse(self.builder.ready)


class TestPostgresDockerRunner(unittest.TestCase):
    """
    Test the docker runner
    """

    @mock.patch('mc.builders.Client')
    def setUp(self, mocked):
        instance = mocked.return_value
        instance.create_container.return_value = {'Id': 'mocked'}
        instance.port.return_value = [{'HostIp': '127.0.0.1', 'HostPort': 1234}]
        instance.containers.return_value = [
            {
                u'Command': u'/entrypoint.sh redis-server',
                u'Created': 1443632967,
                u'Id': u'mocked',
                u'Image': u'redis',
                u'Labels': {},
                u'Names': [u'/livetest-redis-tLJpZ'],
                u'Ports': [{u'PrivatePort': 6379, u'Type': u'tcp'}],
                u'Status': u'Up About a minute'
            }
        ]
        self.instance = instance
        self.builder = PostgresDockerRunner(network_mode="host")

    def test_ready(self):
        """
        Tests the health check of the service
        """

        with mock.patch('mc.builders.create_engine') as mocked:
            engine_instance = mocked.return_value
            engine_instance.connect.side_effect = OperationalError('', '', '', '')
            self.assertFalse(self.builder.ready)

        with mock.patch('mc.builders.create_engine') as mocked:
            engine_instance = mocked.return_value
            engine_instance.connect.return_value = ''
            self.assertTrue(self.builder.ready)
