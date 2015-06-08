"""
Application factory
"""

import logging.config
import os
from mc.models import db
from celery import Celery
import jinja2
from flask import Flask
from flask.ext.restful import Api
from mc.views import GithubListener


def create_app(name="mission-control"):
    """
    Create the application

    :param name: name of the application
    :return: flask.Flask application
    """

    app = Flask(name, static_folder=None)
    app.url_map.strict_slashes = False

    # Load config and logging
    load_config(app)
    logging.config.dictConfig(
        app.config['MC_LOGGING']
    )

    # Register extensions
    api = Api(app)
    api.add_resource(GithubListener, '/webhooks')
    db.init_app(app)

    return app


def create_celery(app=None):
    """
    The function creates a new Celery object, configures it with the broker
    from the application config, updates the rest of the Celery config from the
    Flask config and then creates a subclass of the task that wraps the task
    execution in an application context.
    http://flask.pocoo.org/docs/0.10/patterns/celery/
    :param app: flask.Flask application instance or None
    :return: configured celery.Celery instance
    """
    if app is None:
        app = create_app()

    celery = Celery(
        app.import_name,
        broker=app.config.get('CELERY_BROKER_URL')
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


def create_jinja2(template_dir=None):
    """
    create a jinja2 environment using the FileSystemLoader

    :param template_dir: absolute or relative path with which to look for
        templates
    :return: jinja2.Environment instance
    """
    if template_dir is None:
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    loader = jinja2.FileSystemLoader(template_dir)
    return jinja2.Environment(loader=loader)


def load_config(app, basedir=os.path.dirname(__file__)):
    """
    Loads configuration in the following order:
        1. config.py
        2. local_config.py (ignore failures)
        3. consul (ignore failures)
    :param app: flask.Flask application instance
    :param basedir: base directory to load the config from
    :return: None
    """

    app.config.from_pyfile(os.path.join(basedir, 'config.py'))

    try:
        app.config.from_pyfile(os.path.join(basedir, 'local_config.py'))
    except IOError:
        app.logger.warning("Could not load local_config.py")

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, use_reloader=False)
