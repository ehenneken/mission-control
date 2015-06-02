"""
Test webservices
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)
import unittest
import app
from flask.ext.testing import TestCase

class TestWebservices(TestCase):
    """
    Tests that each route is an http response
    """
  
    def create_app(self):
        """
        Create the wsgi application
        """
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        return app_

if __name__ == '__main__':
    unittest.main(verbosity=2)
