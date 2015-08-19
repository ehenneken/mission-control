"""
Test webservices
"""
import mock
from mc import app
from mc.models import Commit, db
from flask.ext.testing import TestCase
from flask import url_for

class TestEndpoints(TestCase):
    """
    Tests http endpoints
    """
  
    def create_app(self):
        """
        Create the wsgi application
        """
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app_.config['MC_LOGGING'] = {}
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

    def test_githublistener_endpoint(self):
        """
        Test basic functionality of the GithubListener endpoint
        """
        url = url_for('GithubListener'.lower())
        r = self.client.get(url)
        self.assertStatus(r, 405)  # Method not allowed
        r = self.client.post(url)
        self.assertStatus(r, 400)  # No signature given

    def test_githublistener_post_return(self):
        """
        Test the overall response of the GithubListener post endpoint
        """

        # Without tag
        commit = Commit(
            repository='git-repo',
            commit_hash='git-hash'
        )
        with mock.patch('mc.views.GithubListener') as gh_mock, \
                mock.patch('mc.tasks.build_docker') as bd_mock:

            gh_mock.parse_github_payload.return_value = commit
            bd_mock.delay.return_value = None

            url = url_for('GithubListener'.lower())
            r = self.client.post(url)
        self.assertEqual(r.json['received'], 'git-repo@git-hash, tag:None')

        # With tag
        commit.tag = 'v1.0.0'
        with mock.patch('mc.views.GithubListener') as gh_mock, \
                mock.patch('mc.tasks.build_docker') as bd_mock:

            gh_mock.parse_github_payload.return_value = commit
            bd_mock.delay.return_value = None

            url = url_for('GithubListener'.lower())
            r = self.client.post(url)
        self.assertEqual(r.json['received'], 'git-repo@git-hash, tag:v1.0.0')
