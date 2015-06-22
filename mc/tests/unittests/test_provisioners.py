"""
Test provisioners.py
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest
from flask import current_app
from mc.provisioners import ScriptProvisioner, PostgresProvisioner
from mc.exceptions import UnknownServiceError
from mc.app import create_app


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
        services = ["adsws", "metrics", "biblib"]
        P = PostgresProvisioner(services)
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


if __name__ == '__main__':
    unittest.main(verbosity=2)