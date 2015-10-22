"""
Test provisioners.py
"""
import unittest
from flask import current_app
from mc.builders import GunicornDockerRunner
from mc.provisioners import ScriptProvisioner, PostgresProvisioner, \
    ConsulProvisioner, TestProvisioner
from mc.exceptions import UnknownServiceError
from mc.app import create_app
from mock import Mock, patch


class TestScriptProvisioner(unittest.TestCase):
    """
    Test the ScriptProvisioner by calling basic shell scripts and ensuring
    that their status codes are 0
    """

    def test_call(self):
        """
        run `echo "hello world"`, check for 0 returncode
        """
        scripts = [
            ["echo", "hello world"],
            ["echo", "hello world again"],
        ]
        provisioner = ScriptProvisioner(scripts=scripts)
        provisioner()
        for process in provisioner.processes.values():
            self.assertEqual(process.returncode, 0, msg=process)


class TestPostgresProvisioner(unittest.TestCase):
    """
    Test the PostgresProvisioner
    """

    def test_unknown_service(self):
        """
        Passing an unknown service should raise UnknownServiceError
        """
        with self.assertRaisesRegexp(UnknownServiceError, "unknown-service"):
            PostgresProvisioner("unknown-service")

    def test_templates(self):
        """
        Test that the templates are rendered after init on a known service;
        The attribute self.services should be a dict with
        key,value = service, template
        the attribute directory should point to the base template directory
        """
        container = Mock(port=5437, host='localhost')
        services = ['adsws', 'metrics', 'biblib']

        P = PostgresProvisioner(services, container=container)
        self.assertIsInstance(P.services, dict)
        self.assertListEqual(services, P.services.keys())
        for s in services:
            self.assertIsInstance(P.services[s], basestring)
            self.assertIn(
                s,
                P.services[s],
                msg="{} not in {}".format(s, P.services[s])
            )
        self.assertTrue(P.directory.endswith('templates/postgres'))

    def test_get_cli_params(self):
        """
        This @staticmethod should return a string.
        The function should work both with and without an application context
        """
        cli = PostgresProvisioner.get_cli_params()
        self.assertIsInstance(cli, basestring)

        with create_app().app_context():
            self.assertEqual(cli, PostgresProvisioner.get_cli_params())
            # Delete the requires config value to see if the method tries to
            # access it. Expect KeyError
            with self.assertRaises(KeyError):
                del current_app.config['DEPENDENCIES']['POSTGRES']
                PostgresProvisioner.get_cli_params()


class TestConsulProvisioner(unittest.TestCase):
    """
    Test that consul is provisioned correctly
    """

    def test_unknown_service(self):
        """
        Consul should not provision config values for unknown services.
        """
        with self.assertRaisesRegexp(UnknownServiceError, 'unknown-service'):
            ConsulProvisioner('unknown-service')

    def test_discovers_services_from_templates(self):
        """
        Provisioner should auto-discover which services it knows about.
        """
        known_services = ['adsws', 'biblib']
        discovered_services = ConsulProvisioner.known_services()
        for item in known_services:
            self.assertIn(item, discovered_services)

    def test_templates(self):
        """
        Test that the templates are rendered after init on a known service;
        The attribute self.services should be a dict with
        key,value = service, template
        the attribute directory should point to the base template directory
        """

        services = ['adsws']
        container = Mock(running_port=8500, running_host='localhost')

        P = ConsulProvisioner(services, container=container)
        self.assertIsInstance(P.services, dict)
        self.assertListEqual(services, P.services.keys())
        for s in services:
            self.assertIsInstance(P.services[s], basestring)
            self.assertIn(
                s,
                P.services[s],
                msg="{} not in {}".format(s, P.services[s])
            )
        ends_with = 'templates/consul'
        self.assertTrue(
            P.directory.endswith(ends_with),
            msg='{} does not endwith {}'.format(P.directory, ends_with)
        )

    def test_get_requirement_params(self):
        """
        This @statmicmethod should return a dictionary.
        The function should work both with and without and application context.
        It retreives the relevant parameters from postgres, for consul.
        """

        consul_mock = Mock(running_port=8500)
        postgres_mock = Mock(running_host='localhost', running_port=5437)
        redis_mock = Mock(running_host='localhost', running_port=6739)

        P = ConsulProvisioner(container=consul_mock,
                              services=['adsws'],
                              requirements={'postgres': postgres_mock, 'redis': redis_mock}
                              )

        db_params = P.get_db_params()
        self.assertEqual(db_params['HOST'], 'localhost')
        self.assertEqual(db_params['PORT'], 5437)

        cache_params = P.get_cache_params()
        self.assertEqual(cache_params['HOST'], 'localhost')
        self.assertEqual(cache_params['PORT'], 6739)


class TestTestProvisioner(unittest.TestCase):
    """
    Test that the tests are provisioned correctly
    """
    @patch('mc.provisioners.Client')
    def test_get_config_for_adsrex(self, mocked):
        """
        Tests how it gets the relevant config variables
        """
        instance = mocked.return_value
        instance.port.return_value = [{'HostIp': '127.0.0.1', 'HostPort': 1234}]
        instance.containers.return_value = [
            {
                u'Command': u'/entrypoint.sh redis-server',
                u'Created': 1443632967,
                u'Id': u'mocked',
                u'Image': u'redis',
                u'Labels': {},
                u'Names': [u'/livetest-adsws-tLJpZ'],
                u'Ports': [{u'PrivatePort': 80, u'Type': u'tcp'}],
                u'Status': u'Up About a minute'
            }
        ]

        test_provisioner = TestProvisioner()
        params = test_provisioner.get_properties_adsrex()
        self.assertEqual(params['api_port'], 1234)
        self.assertEqual(params['api_host'], '127.0.0.1')

    @patch('mc.provisioners.Client')
    def test_templates(self, mocked):
        """
        Test that the templates are rendered after init on a known service;
        The attribute self.services should be a dict with
        key,value = service, template
        the attribute directory should point to the base template directory
        """
        instance = mocked.return_value
        instance.port.return_value = [{'HostIp': '127.0.0.1', 'HostPort': 1234}]
        instance.containers.return_value = [
            {
                u'Command': u'/entrypoint.sh redis-server',
                u'Created': 1443632967,
                u'Id': u'mocked',
                u'Image': u'redis',
                u'Labels': {},
                u'Names': [u'/livetest-adsws-tLJpZ'],
                u'Ports': [{u'PrivatePort': 80, u'Type': u'tcp'}],
                u'Status': u'Up About a minute'
            }
        ]

        config = {
            'adsrex': {
                'api': 'http://127.0.0.1:1234'
            }
        }
        services = ['adsrex']

        P = TestProvisioner(services=services)
        self.assertIsInstance(P.services, dict)
        self.assertListEqual(services, P.services.keys())

        for s in services:
            self.assertIsInstance(P.services[s], basestring)

            for item in config[s].values():
                self.assertIn(
                    item,
                    P.services[s],
                    msg='{} not in {}'.format(item, P.services[s])
                )

            ends_with = 'templates/testenv'
            self.assertTrue(
                P.directories[s].endswith(ends_with),
                msg='{} does not endwith {}'.format(P.directories[s], ends_with)
            )
