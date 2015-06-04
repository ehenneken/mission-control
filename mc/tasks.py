"""
Tasks that should live outside of the request/response cycle
"""

from flask import current_app
from docker import Client
from jinja2 import TemplateNotFound
from mc.app import create_celery, create_jinja2
from mc.models import db, Build

celery = create_celery()
templates = create_jinja2()


def render_template(commit):
    """
    renders a jinija2 template based on the commit

    :param commit: commit from which to render a template
    :type commit: models.Commit instance
    :return: context-rendered template
    :rtype string
    """
    try:
        t = templates.get_template(
            'docker/dockerfiles/{}.dockerfile.template'.format(commit.repository)
        )
    except TemplateNotFound, e:
        current_app.logger.error(
            "Template for repo {} not found {}".format(commit.repository, e)
        )
        raise
    return t.render(commit=commit)

@celery.task()
def build_docker(commit):
    """
    Task responsible for building a docker image from a commit, and pushing
    that image to a remote repository for storage

    :param commit: commit from which to build
    :type commit: models.Commit instance
    :return: None
    """
    pass









