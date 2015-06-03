"""
Test factory (app.py)
"""

import sys
import os
PROJECT_HOME = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../../'))
sys.path.append(PROJECT_HOME)

import unittest
from mc import app
from flask import Flask
from celery import Celery
import jinja2


class TestFactory(unittest.TestCase):
    """
    Test app.py create_* factory functions
    """

    def test_create_app(self):
        a = app.create_app(name='unittest')
        self.assertIsInstance(a, Flask)
        self.assertEqual(a.import_name, 'unittest')

    def test_create_celery(self):
        a = app.create_app(name='unittest')
        celery = app.create_celery(app=a)
        self.assertIsInstance(celery, Celery)
        self.assertEqual(celery.main, 'unittest')

    def test_create_jinja2(self):
        e = app.create_jinja2()
        self.assertIsInstance(e, jinja2.Environment)
        self.assertIsInstance(e.loader, jinja2.FileSystemLoader)

if __name__ == '__main__':
    unittest.main(verbosity=2)