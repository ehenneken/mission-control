"""
Test builders
"""
import requests
import unittest
import time
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
                    "image": "redis",
                    "callback": None,
                },
                {
                    "name": "consul",
                    "image": "adsabs/consul:v1.0.0",
                    "callback": ConsulProvisioner(services=services),
                },
                {
                    "name": "postgres",
                    "image": "postgres",
                    "callback": PostgresProvisioner(services=services),
                }
            ]
        }

    def test_start_test_environment_task(self):
        """
        Tests that the environment is correctly setup, the containers are
        running and provisioned.
        """

        start_test_environment(test_id='livetests', config=self.config)

        cli = Client(base_url='unix://var/run/docker.sock')

        while True:
            consul_id = [i for i in cli.containers() if 'consul' in i['Image']][0]['Id']
            if len(consul_id) == 0:
                time.sleep(1)
            else:
                break

        print cli.port(consul_id, 8500)
        consul_port = cli.port(consul_id, 8500)[0]['HostPort']
        consul_host = cli.port(consul_id, 8500)[0]['HostIp']

        while requests.get('http://{}:{}'.format(consul_host, consul_port)).status_code != 200:
            time.sleep(1)

        session = Consul(port=consul_port)
        self.assertEqual(
            session.kv.get('config/adsws/staging/DEBUG'),
            False
        )

