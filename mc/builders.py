from mc.app import create_jinja2
from mc.utils import timed
from mc.exceptions import BuildError, TimeOutError, UnknownServiceError
from mc.provisioners import ConsulProvisioner, PostgresProvisioner, SolrProvisioner, TestProvisioner
from flask import current_app
from docker import Client
from sqlalchemy.exc import OperationalError
from sqlalchemy import create_engine
from redis import Redis, ConnectionError

import os
import io
import mc.config as config
import logging
import tarfile
import requests

DOCKER_BRIDGE = '172.17.42.1'


class ECSBuilder(object):
    """
    Responsible for building and creating an AWS-ecs deployment
    """

    class DockerContainer(object):
        """
        Represents a docker container as defined in `Dockerrun.aws.json`.
        """

        def __init__(self, build, environment, memory, namespace='adsabs',
                     portmappings=None):
            """
            :param build: mc.models.Build
            :param environment: string environment e.g. "staging"
            :param memory: int memory in MB (100)
            :param namespace: the docker image namespace
            :param portmappings: {"containerPort":80, "hostPort":8080}
            :type portmappings: dict or None
            """
            self.build = build
            self.environment = environment
            self.memory = memory
            self.namespace = namespace
            self.name = build.commit.repository
            self.portmappings = portmappings

        @property
        def image(self):
            """
            getter for the string formatted docker image as hosted on dockerhub
            """
            return "{}/{}:{}".format(
                self.namespace,
                self.name,
                self.build.commit.tag if self.build.commit.tag
                else self.build.commit.commit_hash
            )

    def __init__(self, containers, family):
        """
        :param containers: list of ECSBuilder.DockerContainer instances
        :param family: ECS-required "family" field
        """
        self.containers = containers
        self.templates = create_jinja2()
        self.family = family

    def render_template(self):
        """
        renders the `Dockerrun.aws.json` template
        """
        apps = [{
            'name': container.name,
            'image': container.image,
            'environment': container.environment,
            'memory': container.memory,
            'portMappings': container.portmappings
        } for container in self.containers]

        t = self.templates.get_template('aws/containers.template')
        return t.render(apps=apps, family=self.family)


class DockerImageBuilder(object):
    """
    Class responsible for finding the correct templates, rendering them,
    creating a build context, executing docker build, and executing docker push
    """

    def __init__(self, commit, namespace="adsabs"):
        self.commit = commit
        self.repo = commit.repository
        self.templates = create_jinja2()
        self.tag = "{}/{}:{}".format(
            namespace,
            self.repo,
            self.commit.tag if self.commit.tag else self.commit.commit_hash
        )
        self.files = []
        self.tarfile = None
        self.built = False
        self.pushed = False

    def run(self):
        """
        Shortcut method that calls all the methods in the correct order
        to build and push an image
        """
        self.render_templates()
        self.create_docker_context()
        self.build()
        self.push()

    def render_templates(self):
        """
        Finds the templates using the app's create_jinja2 loader
        """

        # dockerfile
        t = self.templates.get_template(
            'docker/dockerfiles/{}.dockerfile.template'.format(
                self.repo
            )
        )
        self.files.append({
            'name': 'Dockerfile',
            'content': t.render(commit=self.commit),
        })

        # gunicorn
        t = self.templates.get_template(
            'docker/gunicorn/gunicorn.conf.py'
        )
        self.files.append({
            'name': 'gunicorn.conf.py',
            'content': t.render(),
        })

        t = self.templates.get_template(
            'docker/gunicorn/gunicorn.sh'
        )
        self.files.append({
            'name': 'gunicorn.sh',
            'content': t.render(),
            'mode': 0555,
        })

        # nginx
        t = self.templates.get_template(
            'docker/nginx/app.nginx.conf'
        )
        self.files.append({
            'name': 'app.nginx.conf',
            'content': t.render(),
        })

        t = self.templates.get_template(
            'docker/nginx/nginx.sh'
        )
        self.files.append({
            'name': 'nginx.sh',
            'content': t.render(),
            'mode': 0555,
        })

        # cron/, etc/ iif there exists a `self.repo` directory
        def _filter(p):
            return ("cron/" in p or "etc/" in p) and (self.repo in p) and \
                   (not os.path.basename(p).startswith('.'))

        for t in self.templates.list_templates(
                filter_func=_filter):

            self.files.append({
                'name': os.path.basename(t),
                'content': self.templates.get_template(t).render(),
            })

    def create_docker_context(self):
        """
        Creates an in-memory tarfile that will be used as the docker context
        """

        self.tarfile = io.BytesIO()

        with tarfile.open(fileobj=self.tarfile, mode="w|") as tar:
            for f in self.files:
                tarinfo = tarfile.TarInfo(f['name'])
                tarinfo.size = len(f['content'])
                if 'mode' in f:
                    tarinfo.mode = f['mode']
                tar.addfile(tarinfo, io.BytesIO(f['content'].encode('utf-8')))
        self.tarfile.seek(0)  # Reset from EOF

    def build(self):
        """
        runs docker build with the tarfile context
        """
        docker = Client(version='auto')
        status = docker.build(
            fileobj=self.tarfile,
            custom_context=True,
            tag=self.tag,
            pull=True,
            nocache=True,
            rm=True,
        )

        for line in status:  # This effectively blocks on `docker build`
            try:
                current_app.logger.debug(line)
            except RuntimeError:  # Outside of application context
                print line
        if "successfully built" not in line.lower():
            raise BuildError("Failed to build {}: {}".format(self.tag, line))

        self.built = True

    def push(self):
        """
        Runs docker push
        """

        # Need to set HOME such that the .dockercfg file is read from
        # a non-default location.
        # See https://github.com/docker/docker/issues/6141
        try:
            dh = current_app.config.get('DOCKER_HOME')
            if dh:
                #  Is it safe to not reset home after we're done here?
                os.environ['HOME'] = dh
        except RuntimeError:
            pass

        docker = Client(version='auto')
        status = docker.push(
            self.tag,
            stream=True,
        )

        for line in status:  # This effectively blocks on `docker push`
            try:
                current_app.logger.debug(line)
            except RuntimeError:  # Outside of application context
                print line

        if not ("pushing tag" in line.lower() or "digest: sha256" in line.lower()):
            raise BuildError("Failed to push {}: {}".format(self.tag, line))

        self.pushed = True


class DockerRunner(object):
    """
    Responsible for pulling a docker image, creating a container, running
    the container, then tearing down the container
    """
    service_name = None

    def __init__(self, image, name, command=None, environment=None, **kwargs):
        """
        :param image: full name of the docker image to pull
        :param name: name of the container in `docker run --name`
        :param command: command for the container in `docker run <> command`
        :param enviroment: environment variables in the container
        :param mem_limit: Memory limit to enforce on the container
        :param kwargs: keyword args to pass direclty to
            docker.utils.create_host_config
        """
        self.image = image
        self.name = name
        self.command = command
        self.environment = environment
        self.running_properties = None
        self.time_out = 30
        self.pull = kwargs.get('pull', True)
        self.running_port = None
        self.running_host = None
        self.client = Client(version='auto')

        kwargs.pop('build_requirements', '')
        self.host_config = self.client.create_host_config(**kwargs)
        self.container = None

        try:
            self.logger = current_app.logger
        except RuntimeError:  # Outside of application context
            self.logger = logging.getLogger("{}-builder".format(self.name))
            self.logger.setLevel(logging.DEBUG)

        self.setup()

    def setup(self):
        """
        Pull the image and create a container with host_config
        """

        exists = [i for i in self.client.images() if self.image in i['RepoTags']]

        # Only pull the image if we don't have it
        if not exists or self.pull:
            self.client.pull(self.image)
            self.logger.debug("Pulled {}".format(self.image))

        self.container = self.client.create_container(
            image=self.image,
            host_config=self.host_config,
            name=self.name,
            command=self.command,
            environment=self.environment
        )
        self.logger.debug("Created container {}".format(self.container['Id']))

    def start(self, callback=None):
        """
        Starts the container, and optionally executes a callback that is passed
        the container's info
        :param callback: Optional callback function that is called after
            the container is up. Useful for running more fine-grained container
            provisioning.
        :return: None
        """
        self.logger.debug('Starting container {}'.format(self.image))
        response = self.client.start(container=self.container['Id'])
        if response:
            self.logger.warning(response)

        self.logger.debug('Checking if {} service is ready'.format(self.name))
        timed(lambda: self.running, time_out=30, exit_on=True)
        timed(lambda: self.ready, time_out=30, exit_on=True)

        self.logger.debug('Service {} is ready'.format(self.name))
        if callable(callback):
            callback(container=self.container)

        self.logger.debug('Startup of {} complete'.format(self.name))

    def teardown(self):
        """
        Stops and removes the docker container.
        :return: None
        """
        response = self.client.stop(container=self.container['Id'])
        if response:
            self.logger.warning(response)

        response = self.client.remove_container(container=self.container['Id'])
        if response:
            self.logger.warning(response)

        try:
            timed(lambda: self.running, time_out=self.time_out, exit_on=False)
        except TimeOutError:
            self.logger.warning(
                'Container teardown timed out, may still be running {}'
                .format(self.container)
            )
            print 'Timeout'

    @property
    def ready(self):
        """
        Check the service is ready
        """
        return True

    @property
    def running(self):
        """
        Determine if the container started
        :return: boolean
        """
        running_properties = [i for i in self.client.containers() if i['Id'] == self.container['Id']]

        if len(running_properties) == 0 or 'Up' not in running_properties[0].get('Status', ''):
            return False
        else:
            self.logger.info('Docker container {} running'.format(self.image))
            self.running_properties = running_properties

            if self.service_name:
                try:
                    running = self.client.port(self.container, config.DEPENDENCIES[self.service_name.upper()]['PORT'])
                    self.running_host = running[0]['HostIp']
                    self.running_port = running[0]['HostPort']
                except KeyError:
                    pass

            return True

    def provision(self, services, requirements=None):
        """
        Run the provisioner of this class for a set of services
        :param services: list of services
        """
        if hasattr(self, 'service_provisioner'):
            provisioner = self.service_provisioner(services=services,
                                                   container=self,
                                                   requirements=requirements)
            provisioner()


class RedisDockerRunner(DockerRunner):
    """
    Wrapper for redis specific commands
    """

    service_name = 'redis'

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = config.DEPENDENCIES[self.service_name.upper()]['IMAGE'] if not image else image
        name = self.service_name if not name else name

        kwargs.setdefault('mem_limit', '50m')
        kwargs.setdefault('port_bindings', {6379: None})

        super(RedisDockerRunner, self).__init__(image, name, command, **kwargs)

    @property
    def ready(self):
        """
        Check the service is ready
        """
        if not self.running:
            return False

        try:
            rs = Redis(host=self.running_host, port=self.running_port)
            rs.client_list()
            return True
        except ConnectionError:
            return False
        except Exception as error:
            self.logger.error('Unexpected error: {}'.format(error))


class GunicornDockerRunner(DockerRunner):
    """
    Wrapper for redis specific commands
    """

    service_name = 'gunicorn'

    def __init__(self, image=None, name=None, command=None, environment=None, **kwargs):

        gunicorn_environment = {
            'CONSUL_HOST': DOCKER_BRIDGE,
            'CONSUL_PORT': kwargs.get('consul_port', 8500),
            'SERVICE': kwargs.get('service_name', 'generic_service'),
            'ENVIRONMENT': kwargs.get('service_environment', 'staging')
        }

        kwargs.setdefault('port_bindings', {80: None})
        kwargs.setdefault('dns', [DOCKER_BRIDGE])
        super(GunicornDockerRunner, self).__init__(
            image,
            name,
            command,
            environment=gunicorn_environment if not environment else environment,
            **kwargs
        )

    @property
    def ready(self):
        """
        Check the service is ready
        """
        if not self.running:
            return False

        try:
            response = requests.get(
                'http://{host}:{port}/'.format(
                    host=self.running_host,
                    port=self.running_port
                )
            )
        except requests.ConnectionError:
            return False

        if response.status_code == 200:
            return True
        elif response.status_code >= 500:
            return False
        else:
            self.logger.warning('Unexpected error code from {}: {}'.format(self.image, response.status_code))
            return True


class ConsulDockerRunner(DockerRunner):
    """
    Wrapper for consul specific commands
    """

    service_name = 'consul'
    service_provisioner = ConsulProvisioner

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = config.DEPENDENCIES[self.service_name.upper()]['IMAGE'] if not image else image
        image = config.DEPENDENCIES[self.service_name.upper()]['IMAGE'] if not image else image
        name = self.service_name if not name else name
        command = ['-server', '-bootstrap'] if not command else command

        kwargs.setdefault('mem_limit', '50m')
        kwargs.setdefault('port_bindings', {8500: None, '53/tcp': 53, '53/udp': 53})

        super(ConsulDockerRunner, self).__init__(image, name, command, **kwargs)

    @property
    def ready(self):
        """
        Check the service is ready
        """

        if not self.running:
            return False

        try:
            response = requests.get(
                'http://{}:{}/v1/kv/health'.format(
                    self.running_host,
                    self.running_port
                )
            )
        except requests.ConnectionError:
            return False

        if response.status_code == 404:
            return True
        elif response.status_code == 500:
            return False
        else:
            return False


class RegistratorDockerRunner(DockerRunner):
    """
    Wrapper for registrator specific commands
    """

    service_name = 'registrator'

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = config.DEPENDENCIES[self.service_name.upper()]['IMAGE'] if not image else image
        name = self.service_name if not name else name
        requirements = kwargs.pop('build_requirements', {})
        try:
            consul = requirements['consul']
            consul_port = consul.running_port
        except KeyError:
            consul_port = 8500
        command = ['-ip', DOCKER_BRIDGE, '-resync', '10', 'consul://{}:{}'.format(DOCKER_BRIDGE, consul_port), '-bootstrap'] if not command else command

        binds = {
            '/var/run/docker.sock': {
                'bind': '/tmp/docker.sock',
                'mode': 'rw',
            }
        }

        kwargs.setdefault('mem_limit', '50m')
        kwargs.setdefault('binds', binds)

        super(RegistratorDockerRunner, self).__init__(image, name, command, **kwargs)

    @property
    def ready(self):
        """
        No ready function
        """
        return self.running


class PostgresDockerRunner(DockerRunner):
    """
    Wrapper for postgres specific commands
    """

    service_name = 'postgres'
    service_provisioner = PostgresProvisioner

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = config.DEPENDENCIES[self.service_name.upper()]['IMAGE'] if not image else image
        name = self.service_name if not name else name

        kwargs.setdefault('mem_limit', '50m')
        kwargs.setdefault('port_bindings', {5432: None})

        super(PostgresDockerRunner, self).__init__(image, name, command, **kwargs)

    @property
    def ready(self):
        """
        Check the service is ready
        :return: boolean
        """

        postgres_uri = 'postgresql://postgres:@{host}:{port}'.format(
            host=self.running_host,
            port=self.running_port
        )

        try:
            engine = create_engine(postgres_uri)
            engine.connect()
            return True
        except OperationalError as e:
            return False


class SolrDockerRunner(DockerRunner):
    """
    Wrapper for redis specific commands
    """

    service_name = 'solr'
    service_provisioner = SolrProvisioner

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = config.DEPENDENCIES[self.service_name.upper()]['IMAGE'] if not image else image
        name = self.service_name if not name else name

        kwargs.setdefault('mem_limit', '800m')
        kwargs.setdefault('port_bindings', {8983: None})

        super(SolrDockerRunner, self).__init__(image, name, command, **kwargs)

    @property
    def ready(self):
        """
        Check the service is ready
        """

        if not self.running:
            return False

        try:
            response = requests.get(
                'http://{}:{}'.format(
                    self.running_host,
                    self.running_port
                )
            )
        except requests.ConnectionError:
            return False

        if response.status_code == 404:
            return True
        elif response.status_code == 500:
            return False
        else:
            return False

    def provision(self, services, requirements=None):
        """
        Override default provisioning behaviour to skip services that are unknown.
        :param services: list of services
        """
        try:
            super(SolrDockerRunner, self).provision(services=services, requirements=requirements)
        except UnknownServiceError as error:
            self.logger.warning('Skipping unknown service: {}'.format(error))
            pass


def docker_runner_factory(image):
    """
    Class factory for the docker runner. Returns a specific class for a specific
    type of service.

    :param image: full name of the docker image to pull
    :type image: basestring

    :return: relevant DockerRunner class
    """

    mapping = {
        'gunicorn': GunicornDockerRunner,
        'redis': RedisDockerRunner,
        'consul': ConsulDockerRunner,
        'postgres': PostgresDockerRunner,
        'registrator': RegistratorDockerRunner,
        'solr': SolrDockerRunner
    }

    for key in mapping:
        if key in image:
            return mapping[key]

    return DockerRunner


class TestRunner(object):
    """
    Class to run generic scripts against a test cluster
    """

    service_provisioner = TestProvisioner

    def __init__(self, test_id, test_services, **kwargs):
        """
        Constructor
        :param test_id: Unique identifier of test environment
        :type test_id: basestring

        :param test_services: list of tests to run and provision
        :type test_services: basestring
        """
        self.test_id = test_id
        self.test_services = test_services
        self.kwargs = kwargs

    def start(self):
        """
        Starts the tests
        """
        test_provision = self.service_provisioner(
            services=self.test_services, **self.kwargs)
        test_provision()
