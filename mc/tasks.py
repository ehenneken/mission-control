"""
Tasks that should live outside of the request/response cycle
"""
import json
import logging
import datetime

from mc.app import create_celery
from mc.models import db, Build, Commit
from mc.builders import DockerImageBuilder, DockerRunner, docker_runner_factory, TestRunner
from mc.utils import get_boto_session
from flask import current_app
from docker import Client
from werkzeug.security import gen_salt
from collections import OrderedDict

celery = create_celery()

logger = logging.getLogger()


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
def start_test_environment(test_id=None, config={}):
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

    if not test_id:
        test_id = gen_salt(5)

    config = OrderedDict(config)

    services = config.setdefault('services', [
        {
            'name': 'graphics_service',
            'repository': 'adsabs',
            'tag': 'dd905b927323e1ecf2a563a80d2bc5d9d98b62b4'
        },
        {
            'name': 'metrics_service',
            'repository': 'adsabs',
            'tag': '36d68b50d46277fb1b6b29e9128e170fe14221c5'
        },
        {
            'name': 'recommender_service',
            'repository': 'adsabs',
            'tag': '1d56dd562a9fb18dad615b510f59be622345665e'
        },
        {
            'name': 'adsws',
            'repository': 'adsabs',
            'tag': '1412043693c94cbed63b59ba7988c69f5433fc2a'
        }
    ])

    dependencies = config.setdefault('dependencies', [
        {
            'name': 'redis',
            'image': 'redis:2.8.21'
        },
        {
            'name': 'postgres',
            'image': 'postgres:9.3',
        },
        {
            'name': 'consul',
            'image': 'adsabs/consul:v1.0.0',
            'requirements': ['redis', 'postgres']
        },
        {
            'name': 'registrator',
            'image': 'gliderlabs/registrator:latest',
            'build_requirements': ['consul']
        }
    ])

    containers = {}

    # Deploy
    logger.info('Starting cluster dependencies...')
    for d in dependencies:
        logger.info('... {}'.format(d['image']))

        builder = docker_runner_factory(image=d['image'])(
            image=d['image'],
            name="{}-{}".format(d['name'], test_id),
            build_requirements={r: containers[r] for r in (d['build_requirements'] if d.get('build_requirements', False) else [])}
        )
        builder.start()
        containers[d['name']] = builder

    # Provision
    logger.info('Provisioning cluster dependencies...')
    for d in dependencies:
        containers[d['name']].provision(
            services=[s['name'].replace('-service', '').replace('_service', '') for s in services],
            requirements={r: containers[r] for r in d.get('requirements', [])}
        )
        logger.info('... {}'.format(d['image']))

    # Required values for services that are based on dependencies
    # We are using the docker0 IP for localhost (of host) in the container
    service_environment = dict(
        CONSUL_HOST='172.17.42.1',
        CONSUL_PORT=containers['consul'].running_port,
        ENVIRONMENT='staging'
    )

    logger.info('Starting services...')
    for s in services:

        logger.info('... {}/{}:{}'.format(
            s['repository'],
            s['name'],
            s['tag']
        ))

        service_environment['SERVICE'] = s['name']

        image = '{repository}/{service}:{tag}'.format(
            repository=s['repository'],
            service=s['name'],
            tag=s['tag']
        )
        builder = docker_runner_factory('gunicorn')(
            image=image,
            name='{}-{}'.format(s['name'], test_id),
            environment=service_environment
        )
        builder.start()

        containers[s['name']] = builder


@celery.task()
def stop_test_environment(test_id=None):
    """
    Stop a running test environment based on its unique id
    :param test_id: unique identifier
    :type test_id: basestring
    """

    docker = Client(version='auto')
    containers = [i['Id'] for i in docker.containers() if [j for j in i['Names'] if test_id in j]]

    for container in containers:
        docker.stop(container=container)
        docker.remove_container(container=container)


@celery.task()
def run_test_in_environment(test_id=None, test_services=['adsrex'], **kwargs):
    """
    Run a suite of tests within the test environment
    :param test_id: unique identifier
    :type test_id: basestring

    :param test_services: which tests to run
    :type test_services: basestring
    """
    tests = TestRunner(test_id=test_id, test_services=test_services, **kwargs)
    tests.start()


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

