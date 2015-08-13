"""
Tasks that should live outside of the request/response cycle
"""
import datetime
from flask import current_app
import json

from mc.app import create_celery
from mc.models import db, Build, Commit
from mc.builders import DockerImageBuilder, DockerRunner
from mc.utils import get_boto_session
from mc.provisioners import PostgresProvisioner

celery = create_celery()

@celery.task()
def register_task_revision(ecsbuild):
    """
    Calls the registerTaskDefinition aws-api endpoint to update a task
    definition based on the ECSBuild.
    This must be called within an app context.
    :param ecsbuild: the dockerrun.aws.json, represented as a ECSBuild or a
        JSON-formatted string
    :type ecsbuild: mc.builders.ECSBuild or basestring
    """
    client = get_boto_session().client('ecs')
    if isinstance(ecsbuild, basestring):
        payload = ecsbuild
    else:
        payload = ecsbuild.render_template()
    client.register_task_definition(**json.loads(payload))


@celery.task()
def update_service(cluster, service, desiredCount, taskDefinition):
    """
    Thin wrapper around boto3 ecs.update_service;
    # http://boto3.readthedocs.org/en/latest/reference/services/ecs.html#ECS.Client.update_service
    :param cluster: The short name or full Amazon Resource Name (ARN) of the cluster that your service is running on. If you do not specify a cluster, the default cluster is assumed.
    :param service: The name of the service that you want to update.
    :param desiredCount: The number of instantiations of the task that you would like to place and keep running in your service.
    :param taskDefinition: The family and revision (family:revision ) or full Amazon Resource Name (ARN) of the task definition that you want to run in your service. If a revision is not specified, the latest ACTIVE revision is used. If you modify the task definition with UpdateService , Amazon ECS spawns a task with the new version of the task definition and then stops an old task after the new version is running.
    """
    client = get_boto_session().client('ecs')
    client.update_service(
        cluster=cluster,
        service=service,
        desiredCount=desiredCount,
        taskDefinition=taskDefinition
    )


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
