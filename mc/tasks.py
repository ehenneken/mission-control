"""
Tasks that should live outside of the request/response cycle
"""
import datetime
from flask import current_app
from boto3.session import Session
import json

from mc.app import create_celery
from mc.models import db, Build, Commit
from mc.builders import DockerImageBuilder, DockerRunner
from mc.provisioners import PostgresProvisioner

celery = create_celery()

@celery.task()
def register_task_revision(ecsbuild):
    """
    Calls the registerTaskDefinition aws-api endpoint to update a task
    definition based on the ECSBuild.
    This must be called within an app context.
    :param ecsbuild: mc.builders.ECSBuilder instance
    """
    session = Session(
        aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY'),
        aws_secret_access_key=current_app.config.get('AWS_SECRET_KEY'),
        region_name=current_app.config.get('AWS_REGION')
    )
    client = session.client('ecs')
    client.register_task_definition(**json.loads(ecsbuild.render_template()))


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
    current_app.logger.info(
        "Build {} status built/pushed {}/{}".format(
            commit.commit_hash, build.built, build.pushed
        )
    )
    db.session.add(build)
    db.session.commit()
