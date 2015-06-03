"""
Tasks that should live outside of the request/response cycle
"""

from flask import current_app
from docker import Client
from mc.app import create_celery
from mc.models import db, Build

celery = create_celery()

@celery.task()
def build(commit):
    """
    Task responsible for building a docker image from a commit, and pushing
    that image to a remote repository for storage

    :param commit: commit from which to build
    :type commit: models.Commit instance
    :return: None
    """
    pass






