"""
Test utilities
"""
import os
import hmac
import json
import mock
import hashlib
import datetime
import unittest

from mc import app
from mc.views import GithubListener
from mc.exceptions import NoSignatureInfo, InvalidSignature, UnknownRepoError, \
    TimeOutError
from mc.tests.stubdata.github_webhook_payload import payload, payload_tag
from mc.models import db, Commit
from mc.utils import ChangeDir, get_boto_session, timed, load_yaml_ordered
from dateutil.tz import tzoffset, tzlocal
from flask.ext.testing import TestCase
from collections import OrderedDict


class TestTimed(unittest.TestCase):
    """
    Test that the timed running of a function behaves correctly
    """

    def test_timed_sucess(self):
        """
        Test it returns if suceeds
        """
        func = lambda: True

        response = timed(func)
        self.assertIsNone(response)

    def test_times_out(self):
        """
        Test it raises if it does not exceed
        """
        func = lambda: False
        with self.assertRaises(TimeOutError):
            timed(func, time_out=1)

    def test_times_success_want_opposite_return_value(self):
        """
        Test it passes for a return value of False
        """
        func = lambda: False
        response = timed(func, exit_on=False)
        self.assertIsNone(response)


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


class TestUtilities(unittest.TestCase):
    """
    Test utility functions in utils.py
    """

    def test_ChangeDir(self):
        """
        ChangeDir context manager should change the directory on enter, and
        revert back to the last direction on exit
        """
        current = os.path.abspath(os.curdir)
        with ChangeDir('~/'):
            self.assertEqual(os.path.abspath(os.curdir), os.path.expanduser('~'))
        self.assertEqual(os.path.abspath(os.curdir), current)

    @mock.patch('mc.utils.Session')
    def test_get_boto_session(self, Session):
        """
        get_boto_session should call Session with the current app's config
        """
        app_ = app.create_app()
        app_.config['AWS_REGION'] = "unittest-region"
        app_.config['AWS_ACCESS_KEY'] = "unittest-access"
        app_.config['AWS_SECRET_KEY'] = "unittest-secret"
        with self.assertRaises(RuntimeError):  # app-context must be available
            get_boto_session()
        with app_.app_context():
            get_boto_session()
        Session.assert_called_with(
            aws_access_key_id="unittest-access",
            aws_secret_access_key="unittest-secret",
            region_name="unittest-region",
        )

    def test_load_yaml_in_ordered_dict(self):
        """
        Test can load a YAML file into an OrderedDict correctly
        """

        yaml = """
        test:
          - name: 1
            tag: 2
            repo: 3
          - name: 4
            tag: 5
            repo: 6
        test2:
          - name: empty
        """

        loaded_yaml = load_yaml_ordered(stream=yaml)
        self.assertIsInstance(loaded_yaml, OrderedDict)

        self.assertEqual('test', loaded_yaml.keys()[0])
        self.assertEqual('test2', loaded_yaml.keys()[1])

        self.assertEqual(loaded_yaml['test'][0]['name'], 1)
        self.assertEqual(loaded_yaml['test'][0]['tag'], 2)
        self.assertEqual(loaded_yaml['test'][0]['repo'], 3)

        self.assertEqual(loaded_yaml['test'][1]['name'], 4)
        self.assertEqual(loaded_yaml['test'][1]['tag'], 5)
        self.assertEqual(loaded_yaml['test'][1]['repo'], 6)


class TestStaticMethodUtilities(TestCase):
    """
    Test standalone staticmethods
    """

    def create_app(self):
        """
        Create the wsgi application
        """
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app_.config['GITHUB_SECRET'] = 'unittest-secret'
        return app_

    def setUp(self):
        """
        setUp and tearDown are run at the start of each test; ensure
        that a fresh database is used for each test.
        """
        db.create_all()

    def tearDown(self):
        """
        setUp and tearDown are run at the start of each test; ensure
        that a fresh database is used for each test.
        """
        db.session.remove()
        db.drop_all()

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

        # Set up fake payload
        r = FakeRequest()
        r.data = payload

        # Unknown repos should raise UnknownRepoError
        with self.assertRaises(UnknownRepoError):
            GithubListener.parse_github_payload(r)

        # Modify the data such that the payload refers to a known repo,
        # assert that the returned models.Commit contains the expected data
        r.data = r.data.replace('"name": "mission-control"', '"name": "adsws"')
        c = GithubListener.parse_github_payload(r)
        self.assertEqual(
            c.commit_hash,
            'bcdf7771aa10d78d865c61e5336145e335e30427'
        )
        self.assertEqual(
            c.tag,
            None
        )
        self.assertEqual(c.author, 'vsudilov')
        self.assertEqual(c.repository, 'adsws')
        self.assertEqual(
            c.message,
            "config: 's/SECRET_KEY/GITHUB_SECRET/g' for webhook secret"
        )
        self.assertEqual(
            c.timestamp,
            datetime.datetime(2015, 6, 3, 12, 26, 57, tzinfo=tzlocal())
        )

        # Assert that a different timeformat returns the expected
        # models.Commit.timestamp value
        r.data = r.data.replace(
            "2015-06-03T12:26:57Z",
            "2015-06-09T18:19:39+02:00"
        )
        c = GithubListener.parse_github_payload(r)
        self.assertEqual(
            c.timestamp,
            datetime.datetime(2015, 6, 9, 18, 19, 39, tzinfo=tzoffset(None, 7200))
        )

        # Re-sending a previously saved commit payload should return that
        # previously saved commit
        db.session.add(c)
        db.session.commit()
        self.assertEqual(len(db.session.query(Commit).all()), 1)
        c2 = GithubListener.parse_github_payload(r)
        db.session.add(c2)
        db.session.commit()
        self.assertEqual(len(db.session.query(Commit).all()), 1)

    def test_parse_github_payload_tag(self):
        """
        Tests that a db.Commit object is created when passed a create event
        example github webhook payload
        """

        # Set up fake payload
        r = FakeRequest()
        r.data = payload_tag

        # Unknown repos should raise UnknownRepoError
        with self.assertRaises(UnknownRepoError):
            GithubListener.parse_github_payload(r)

        # There should be not tag added to the commit, but we should expect
        # the returned model.Commit to be correct
        r.data = r.data.replace('"name": "governor"', '"name": "adsws"')
        r.data = r.data.replace('refs/tags', 'heads/commits')
        print r.data
        c = GithubListener.parse_github_payload(r)
        self.assertEqual(
            c.commit_hash,
            '2a047ead58a3a87b46388ac67fe08c944c3230e0'
        )
        self.assertIsNone(c.tag)
        self.assertEqual(c.author, 'adsabs')
        self.assertEqual(c.repository, 'adsws')
        self.assertEqual(
            c.message,
            "First commit."
        )
        self.assertEqual(
            c.timestamp,
            datetime.datetime(2015, 8, 12, 16, 18, 57, tzinfo=tzoffset(None, -4*60*60))
        )
        db.session.add(c)
        db.session.commit()

        # Now put the tag, the tag should be added to the commit
        r.data = r.data.replace('heads/commits', 'refs/tags')
        c2 = GithubListener.parse_github_payload(r)
        self.assertEqual(
            c2.commit_hash,
            '2a047ead58a3a87b46388ac67fe08c944c3230e0'
        )
        self.assertEqual(
            c2.tag,
            'v1.0.0'
        )
        self.assertEqual(c.id, c2.id)

        # Re-sending a previously saved commit payload should return that
        # previously saved commit
        db.session.add(c)
        db.session.commit()
        self.assertEqual(len(db.session.query(Commit).all()), 1)
        c3 = GithubListener.parse_github_payload(r)
        db.session.add(c3)
        db.session.commit()
        self.assertEqual(len(db.session.query(Commit).all()), 1)
