"""
Tasks that should live outside of the request/response cycle
"""

import datetime
from flask import current_app
from mc.app import create_celery

from mc.models import db, Build, Commit
from mc.builders import DockerBuilder

celery = create_celery()


@celery.task()
def build_docker(commit_id):
    """
    Task responsible for building a docker image from a commit, and pushing
    that image to a remote repository for storage

    :param commit_id: commit integer id from which to build
    :type commit_id: int or basestring
    :return: None
    """

    commit_id = int(commit_id)

    commit = Commit.query.get(commit_id)

    build = Build(
        commit=commit,
        timestamp=datetime.datetime.now(),
    )
    current_app.logger.info("Build created: {}:{}".format(
        commit.repository,
        commit.commit_hash,
    ))

    try:
        builder = DockerBuilder(commit)
        builder.run()
    except Exception, e:
        current_app.logger.exception(e)

    build.built = builder.built
    build.pushed = builder.pushed
    db.session.add(build)
    db.session.commit()
