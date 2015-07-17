"""
Test webservices
"""
from mc import app
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

    def test_githublistener_endpoint(self):
        """
        Test basic functionality of the GithubListener endpoint
        """
        url = url_for('GithubListener'.lower())
        r = self.client.get(url)
        self.assertStatus(r, 405)  # Method not allowed
        r = self.client.post(url)
        self.assertStatus(r, 400)  # No signature given