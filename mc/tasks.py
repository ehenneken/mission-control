"""
Tasks that should live outside of the request/response cycle
"""
import json
import logging
import datetime

from mc.app import create_celery
from mc.models import db, Build, Commit
from mc.config import DOCKER_BRIDGE
from mc.builders import DockerImageBuilder, DockerRunner, docker_runner_factory, TestRunner
from mc.utils import get_boto_session, load_yaml_ordered
from flask import current_app
from docker import Client, errors
from werkzeug.security import gen_salt

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
    :param test_id: identifier of the test
    :type test_id: string
    :param config: Config detailing which versions and services to provision
    :type config: dict
    :return: None
    """

    if not test_id:
        test_id = gen_salt(5)

    if not config:
        with open('mc/.mc.yml') as yaml_file:
            config = load_yaml_ordered(yaml_file)

    services = config.get('services')
    dependencies = config.get('dependencies')

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
            services=[s['name'].replace('-services', '').replace('-service', '').replace('_service', '') for s in services],
            requirements={r: containers[r] for r in d.get('requirements', [])}
        )
        logger.info('... {}'.format(d['image']))

    # Required values for services that are based on dependencies
    # We are using the docker0 IP for localhost (of host) in the container
    service_environment = dict(
        CONSUL_HOST=DOCKER_BRIDGE,
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
        try:
            builder = docker_runner_factory('gunicorn')(
                image=image,
                name='{}-{}'.format(s['name'], test_id),
                environment=service_environment
            )
            builder.start()
            containers[s['name']] = builder

        except errors.NotFound as error:
            logger.error('Service not found, skipping: {}, {}'.format(s, error))


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

    :param kwargs: keyword arguments
    """
    tests = TestRunner(test_id=test_id, test_services=test_services, **kwargs)
    tests.start()


@celery.task()
def run_ci_test(test_id=None, config={}, **kwargs):
    """
    Spin up services and dependencies, run continuous integratioh test, tear down services and dependencies.
    :param test_id: unique identifier
    :type test_id: basestring

    :param config: Config detailing which versions and services to provision
    :type config: dict

    :param kwargs: keyword arguments
    """
    test_id = gen_salt(5) if not test_id else test_id

    if not config:
        with open('mc/.mc.yml') as yaml_file:
            config = load_yaml_ordered(yaml_file)

    services = config.get('services')
    dependencies = config.get('dependencies')
    tests = config.get('tests')

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
    try:
        for d in dependencies:
            containers[d['name']].provision(
                services=[s['name'].replace('-services', '').replace('-service', '').replace('_service', '') for s in services],
                requirements={r: containers[r] for r in d.get('requirements', [])}
            )
            logger.info('... {}'.format(d['image']))

        # Required values for services that are based on dependencies
        # We are using the docker0 IP for localhost (of host) in the container
        service_environment = dict(
            CONSUL_HOST=DOCKER_BRIDGE,
            CONSUL_PORT=containers['consul'].running_port,
            ENVIRONMENT='staging'
        )
    except Exception as error:
        logger.warning('Unexpected error, shutting down ... {}'.format(error))
        for container, name in containers.iteritems():
            logger.info('... {}'.format(name))
            container.teardown()

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
        try:
            builder = docker_runner_factory('gunicorn')(
                image=image,
                name='{}-{}'.format(s['name'], test_id),
                environment=service_environment
            )
            builder.start()
            containers[s['name']] = builder

        except errors.NotFound as error:
            logger.error('Service not found, skipping: {}, {}'.format(s, error))

    # Run the tests
    try:
        logger.info('Running tests: {} [ID: {}]'.format(tests, test_id))
        tests = TestRunner(test_id=test_id, test_services=tests)
        tests.start()
    except Exception as error:
        logger.warning('Unexpected error, continuing to shutdown test: {}'.format(error))

    # Shutdown the test cluster
    logger.info('Shutting down services and dependencies...')
    for name, container in containers.iteritems():
        logger.info('... {}'.format(name))
        try:
            container.teardown()
        except Exception as error:
            logger.warning('... Could not stop: {} '.format(error))


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

