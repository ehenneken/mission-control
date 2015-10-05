"""
Test builders
"""

import unittest

from mc.config import DEPENDENCIES
from mc.provisioners import ConsulProvisioner, PostgresProvisioner
from mc.tasks import start_test_environment
from docker import Client
from consulate import Consul


class TestStartTestEnvironment(unittest.TestCase):
    """
    Test the docker runner
    """

    def setUp(self):

        services = ['adsws']

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
            ]
        }

    def test_start_test_environment_task(self):
        """
        Tests that the environment is correctly setup, the containers are
        running and provisioned.
        """

        start_test_environment(test_id='livetests', config=self.config)

        # Check consul is running
        cli = Client(base_url='unix://var/run/docker.sock')
        consul_id = [i for i in cli.containers() if 'consul' in i['Image']][0]['Id']
        consul_port = cli.port(consul_id, 8500)[0]['HostPort']
        consul_host = cli.port(consul_id, 8500)[0]['HostIp']

        session = Consul(host=consul_host, port=consul_port)
        self.assertEqual(
            session.kv.get('config/adsws/staging/DEBUG'),
            "false"
        )

        # Check postgres is running

        # Check redis is running

        # Check service is running

