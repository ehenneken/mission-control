"""
Test builders
"""

import redis
import unittest

from mc.config import DEPENDENCIES
from mc.tasks import start_test_environment
from docker import Client
from consulate import Consul
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError


class TestStartTestEnvironment(unittest.TestCase):
    """
    Test the docker runner
    """

    def setUp(self):
        """
        Define what we want to start
        """
        self.config = {
            'dependencies': [
                {
                    "name": "redis",
                    "image": DEPENDENCIES['REDIS']['IMAGE'],
                    "callback": None,
                },
                {
                    "name": "consul",
                    "image": DEPENDENCIES['CONSUL']['IMAGE'],
                    "callback": None,
                },
                {
                    "name": "postgres",
                    "image": DEPENDENCIES['POSTGRES']['IMAGE'],
                    "callback": None,
                }
            ],
            'services': [
                {
                    'name': 'adsws',
                    'repository': 'adsabs',
                    'tag': '0596971c755855ff3f9caed2f96af7f9d5792cc2'
                }
            ]
        }

    def tearDown(self):
        """
        Clean up the dependencies and services
        """

        # stop the services
        for d in self.config['dependencies']:
            self.helper_stop_container(d['name'])

        for s in self.config['services']:
            self.helper_stop_container(s['name'])

    @staticmethod
    def helper_get_container_values(name, port):
        """
        Get the properties of the running container
        :param name: name of the container
        :type name: basestring

        :param port: port commonly used
        :type port: int

        :return: dictionary
        """
        cli = Client(base_url='unix://var/run/docker.sock')
        container_id = [i for i in cli.containers() if name in i['Image']][0]['Id']
        info = cli.port(container_id, port)[0]
        container_port = info['HostPort']
        container_host = info['HostIp']

        return dict(port=container_port, host=container_host, id=container_id)

    @staticmethod
    def helper_stop_container(name):
        """
        Stop specified docker container
        :param name: name of the container
        :type name: basestring
        """
        cli = Client(base_url='unix://var/run/docker.sock')
        container = [i for i in cli.containers() if name in i['Image']][0]
        container_id = container['Id']
        container_name = container['Names'][0]

        try:
            cli.stop(container_id)
            cli.remove_container(container_name)
        except Exception:
            pass

    def test_start_test_environment_task(self):
        """
        Tests that the environment is correctly setup, the containers are
        running and provisioned.
        """

        start_test_environment(test_id='livetests', config=self.config)

        # Check redis is running
        redis_info = self.helper_get_container_values('redis', 6379)
        rs = redis.Redis('localhost', port=redis_info['port'])
        try:
            rs.client_list()
        except redis.ConnectionError as e:
            self.fail('Redis cache has not started: {}'.format(e))

        # Check consul is running
        consul_info = self.helper_get_container_values('consul', 8500)
        session = Consul(host=consul_info['host'], port=consul_info['port'])
        self.assertEqual(
            session.kv.get('config/adsws/staging/DEBUG'),
            "false"
        )

        # Check postgres is running
        postgres_info = self.helper_get_container_values('postgres', 5432)
        postgres_uri = 'postgresql://postgres:@{host}:{port}'.format(
            host=postgres_info['host'],
            port=postgres_info['port']
        )
        try:
            engine = create_engine(postgres_uri)
            engine.connect()
        except OperationalError as e:
            self.fail('Postgresql database has not started: {}'.format(e))
