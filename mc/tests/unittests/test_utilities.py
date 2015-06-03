"""
Test utilities
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)
import unittest
from mc import app
from mc.views import GithubListener
from mc.exceptions import NoSignatureInfo, InvalidSignature
import hmac
import hashlib
from flask.ext.testing import TestCase


class TestUtilities(TestCase):
    """
    Tests that each route is an http response
    """

    def create_app(self):
        """
        Create the wsgi application
        """
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app_.config['GITHUB_SECRET'] = 'unittest-secret'
        return app_

    def test_verify_signature(self):
        """
        Ensures that the signature is validated against the github algorithim
        found at https://github.com/github/github-services/blob/f3bb3dd780feb6318c42b2db064ed6d481b70a1f/lib/service/http_helper.rb#L77
        """

        class FakeRequest: pass

        r = FakeRequest()

        r.data = '''{"payload": "unittest"}'''
        h = hmac.new(
            self.app.config['GITHUB_SECRET'],
            msg=r.data,
            digestmod=hashlib.sha1,
        ).hexdigest()
        r.headers = {
            'content-type': 'application/json',
            self.app.config['GITHUB_SIGNATURE_HEADER']: "sha1={}".format(h)
        }

        self.assertTrue(GithubListener.verify_github_signature(r))

        with self.assertRaises(InvalidSignature):
            r.data = ''
            GithubListener.verify_github_signature(r)

        with self.assertRaises(NoSignatureInfo):
            r.headers = {}
            GithubListener.verify_github_signature(r)




if __name__ == '__main__':
    unittest.main(verbosity=2)