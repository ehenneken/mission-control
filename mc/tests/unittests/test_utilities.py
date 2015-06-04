"""
Test utilities
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest
import hmac
import hashlib
import json

from mc import app
from mc.views import GithubListener
from mc.exceptions import NoSignatureInfo, InvalidSignature
from mc.tests.stubdata.github_webhook_payload import payload
from mc.tasks import render_template
from mc.models import Commit

from flask.ext.testing import TestCase
from jinja2 import TemplateNotFound

class FakeRequest:
    """
    A rudimentary mock flask.request object
    """
    def __init__(self):
        self.headers = {}
        self.data = ''

    def get_json(self):
        """
        return json from a string
        """
        self.json = json.loads(self.data)
        return self.json


class TestUtilities(TestCase):
    """
    Test standalone utilities and staticmethods
    """

    def create_app(self):
        """
        Create the wsgi application
        """
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app_.config['GITHUB_SECRET'] = 'unittest-secret'
        return app_

    def test_render_template(self):
        """
        Tests that the mc.tasks.render_template function returns a string that
        contains the incomminig commit's hash and repository
        """
        c = Commit(
            commit_hash="test-hash",
            repository="doesn't exist"
        )
        with self.assertRaises(TemplateNotFound):
            t = render_template(c)

        c.repository = "adsws"
        t = render_template(c)
        self.assertIsInstance(t, basestring)
        self.assertIn(c.repository, t)
        self.assertIn(c.commit_hash, t)


    def test_verify_signature(self):
        """
        Ensures that the signature is validated against the github algorithim
        found at https://github.com/github/github-services/blob/f3bb3dd780feb6318c42b2db064ed6d481b70a1f/lib/service/http_helper.rb#L77
        """

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

    def test_parse_github_payload(self):
        """
        Tests that a db.Commit object is created when passed an example
        github webhook payload
        """
        r = FakeRequest()
        r.data = payload

        c = GithubListener.parse_github_payload(r)
        self.assertEqual(
            c.commit_hash,
            'bcdf7771aa10d78d865c61e5336145e335e30427'
        )
        self.assertEqual(c.author, 'vsudilov')
        self.assertEqual(c.repository, 'mission-control')

if __name__ == '__main__':
    unittest.main(verbosity=2)