"""
Tasks that should live outside of the request/response cycle
"""

from flask import current_app
from docker import Client
from jinja2 import TemplateNotFound
from mc.app import create_celery, create_jinja2
from mc.models import db, Build
from builders import DockerBuilder

celery = create_celery()


@celery.task()
def build_docker(commit):
    """
    Task responsible for building a docker image from a commit, and pushing
    that image to a remote repository for storage

    :param commit: commit from which to build
    :type commit: models.Commit instance
    :return: None
    """
    builder = DockerBuilder(commit)










