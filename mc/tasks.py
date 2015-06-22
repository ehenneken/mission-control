"""
Tasks that should live outside of the request/response cycle
"""

import datetime
from flask import current_app
from mc.app import create_celery

from mc.models import db, Build, Commit
from mc.builders import DockerImageBuilder, DockerRunner
from mc.provisioners import PostgresProvisioner

celery = create_celery()


@celery.task()
def make_test_environment(test_id, config=None):
    """
    Creates the test environment:
      - Run dependency containers
      - Provision dependency containers, if necessary
      - Run the microservices
      - Run the tests
    :param config: Config detailing which versions and services to provision
    :type config: dict
    :return: None
    """

    dependencies = config.setdefault('dependencies', [
        {
            "name": "redis",
            "image": "redis",
            "callback": None,
        },
        {
            "name": "consul",
            "image": "consul",
            "callback": provision_consol,
        },
        {
            "name": "postgres",
            "image": "postgres",
            "callback": provision_psql,
        },
    ])

    for d in dependencies:
        builder = DockerRunner(
            image=d['image'],
            name="{}-{}".format(d['name'], test_id),
        )
        builder.start(callback=d['callback'])



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
        builder = DockerImageBuilder(commit)
        builder.run()
    except Exception, e:
        current_app.logger.exception(e)

    build.built = builder.built
    build.pushed = builder.pushed
    db.session.add(build)
    db.session.commit()
