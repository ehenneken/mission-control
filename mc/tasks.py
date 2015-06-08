"""
Tasks that should live outside of the request/response cycle
"""

import datetime
from flask import current_app
from mc.app import create_celery
from mc.models import db, Build
from mc.builders import DockerBuilder
from flask import Flask

celery = create_celery(Flask('test'))


@celery.task()
def build_docker(commit):
    """
    Task responsible for building a docker image from a commit, and pushing
    that image to a remote repository for storage

    :param commit: commit from which to build
    :type commit: models.Commit instance
    :return: None
    """

    DockerBuilder(commit).run()
    build = Build(
        commit=commit,
        timestamp=datetime.datetime.now(),
    )
    db.session.add(build)
    db.session.commit()
    current_app.logger.info("Build {} created: {}:{}".format(
        build.id,
        commit.repository,
        commit.commit_hash,
    ))