"""
Test provisioners.py
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest
from mc.provisioners import ScriptProvisioner, PostgresProvisioner
from mc.exceptions import UnknownServiceError


class TestScriptProvisioner(unittest.TestCase):
    """
    Test the ScriptProvisioner by calling a basic shell script and ensuring
    that its status code is 0
    """

    def test_call(self):
        """
        run `echo "hello world"`, check for 0 returncode
        """
        provisioner = ScriptProvisioner(script=["echo", "hello world"])
        provisioner()
        self.assertEqual(provisioner.process.returncode, 0)


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


if __name__ == '__main__':
    unittest.main(verbosity=2)