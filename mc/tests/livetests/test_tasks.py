"""
Test builders
"""

import redis
import requests
import unittest

from mc.tasks import start_test_environment, stop_test_environment, run_test_in_environment
from mc.builders import GunicornDockerRunner
from docker import Client, errors
from consulate import Consul
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from collections import OrderedDict


class TestTestEnvironment(unittest.TestCase):
    """
    Test the docker runner
    """

    def setUp(self):
        """
        Define what we want to start
        """

        self.config = OrderedDict({})

        services = self.config.setdefault('services', [
                {
                    'name': 'adsws',
                    'repository': 'adsabs',
                    'tag': '0596971c755855ff3f9caed2f96af7f9d5792cc2'
                }
            ])

        dependencies = self.config.setdefault('dependencies', [
            {
                'name': 'redis',
                'image': 'redis:2.8.21'
            },
            {
                'name': 'postgres',
                'image': 'postgres:9.3',
            },
            {
                'name': 'consul',
                'image': 'adsabs/consul:v1.0.0',
                'requirements': ['redis', 'postgres']
            },
            {
                'name': 'registrator',
                'image': 'gliderlabs/registrator:latest',
                'build_requirements': ['consul']
            },
            {
                'name': 'solr',

            }
        ])

    def tearDown(self):
        """
        Clean up the dependencies and services
        """

        # stop the services
        try:
            for d in self.config['dependencies']:
                self.helper_stop_container(d['name'])
        except:
            pass
        try:
            for s in self.config['services']:
                self.helper_stop_container(s['name'])
        except:
            pass

        try:
            self.helper_stop_container('pythonsimpleserver')
        except:
            pass

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
        print cli.containers
        container_id = [i for i in cli.containers() if name in i['Image']][0]['Id']
        if port:
            info = cli.port(container_id, port)[0]
            container_port = info['HostPort']
            container_host = info['HostIp']
        else:
            container_host = '127.0.0.1'
            container_port = None

        return dict(port=container_port, host=container_host, id=container_id)

    @staticmethod
    def helper_stop_container(name):
        """
        Stop specified docker container
        :param name: name of the container
        :type name: basestring
        """
        cli = Client(base_url='unix://var/run/docker.sock')
        print cli.containers()
        container = [i for i in cli.containers() if name in i['Image']][0]
        container_id = container['Id']
        container_name = container['Names'][0].replace('/', '')

        try:
            cli.stop(container_id)
            cli.remove_container(container_name)
        except Exception as err:
            print err

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

        # Check solr is running
        solr_info = self.helper_get_container_values('solr', 8983)
        response = requests.get('http://{host}:{port}'.format(
                host=solr_info['host'],
                port=solr_info['port']
            )
        )
        self.assertEqual(
            response.status_code,
            404
        )

        # Check consul is running
        consul_info = self.helper_get_container_values('consul', 8500)
        session = Consul(host=consul_info['host'], port=consul_info['port'])
        self.assertEqual(
            session.kv.get('config/adsws/staging/DEBUG'),
            "false"
        )

        self.assertEqual(
            session.kv.get('config/adsws/staging/SQLALCHEMY_DATABASE_URI'),
            '"postgresql+psycopg2://postgres:@{}:{}/adsws"'.format(
                '172.17.42.1',
                postgres_info['port']
            )
        )

        # Check registrator is running
        registrator_info = self.helper_get_container_values('registrator', None)

    def test_stop_test_environment_task(self):
        """
        Test that stop task stops a running test environment
        """

        test_id = '34fe32fdsfdsxxx'
        docker = Client(version='auto')
        image = 'adsabs/pythonsimpleserver:v1.0.0'

        try:
            container = docker.create_container(
                image=image,
                name='livetest-pythonserver-{}'.format(test_id),
            )
        except errors.NotFound:
            docker.pull(image)
            container = docker.create_container(
                image='adsabs/pythonsimpleserver:v1.0.0',
                name='livetest-pythonserver-{}'.format(test_id),
            )
        except Exception as error:
            self.fail('Unknown exception: {}'.format(error))

        docker.start(container=container['Id'])

        stop_test_environment(test_id=test_id)

        self.assertFalse([i for i in docker.containers() if [j for j in i['Names'] if test_id in j]])

    def test_run_test_environment_task(self):
        """
        Test that we can start tests in the test environment
        """
        test_id = '34fef34fsdf'

        name = 'livetest-pythonserver-{}'.format(test_id)

        container = GunicornDockerRunner(
            name=name,
            image='adsabs/pythonsimpleserver:v1.0.0'
        )
        container.start()

        run_test_in_environment(
            test_id=test_id,
            test_services=['adsrex'],
            api_name=name
        )
