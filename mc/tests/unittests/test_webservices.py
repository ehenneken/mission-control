"""
Test webservices
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_HOME)

import unittest
import time
import json
import app
from flask.ext.testing import TestCase
from flask import url_for

class TestWebservices(TestCase):
    """
    Tests that each route is an http response
    """
  
    def create_app(self):
        """
        Create the wsgi application
        """
        app_ = app.create_app()
        return app_

if __name__ == '__main__':
    unittest.main(verbosity=2)
