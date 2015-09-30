from mc.app import create_jinja2
from mc.utils import timed
from mc.exceptions import BuildError, TimeOutError
from flask import current_app
from docker import Client
from docker.utils import create_host_config
from docker.errors import NotFound
from sqlalchemy.exc import OperationalError
from requests import ConnectionError
from consulate import Consul
from sqlalchemy import create_engine

import os
import logging
import tarfile
import io
import mc.config as config


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

    def __init__(self, image, name, command=None, **kwargs):
        """
        :param image: full name of the docker image to pull
        :param name: name of the container in `docker run --name`
        :param command: command for the container in `docker run <> command`
        :param mem_limit: Memory limit to enforce on the container
        :param kwargs: keyword args to pass direclty to
            docker.utils.create_host_config
        """
        self.image = image
        self.name = name
        self.command = command
        self.host_config = create_host_config(**kwargs)
        self.running_properties = None

        self.client = Client(version='auto')
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
        :return: None
        """
        self.client.pull(self.image)
        self.logger.debug("Pulled {}".format(self.image))
        self.container = self.client.create_container(
            image=self.image,
            host_config=self.host_config,
            name=self.name,
            command=self.command
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
        response = self.client.start(container=self.container['Id'])
        if response:
            self.logger.warning(response)

        timed(lambda: self.running, time_out=30)
        timed(lambda: self.ready, time_out=30)

        if callable(callback):
            callback(container=self.container)

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
            self.running_properties = running_properties
            return True


class ConsulDockerRunner(DockerRunner):
    """
    Wrapper for redis specific commands
    """

    service_name = 'consul'

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = 'adsabs/consul:v1.0.0' if not image else image
        name = self.service_name if not name else name
        command = ['-server', '-bootstrap'] if not command else command

        kwargs.setdefault('mem_limit', '50m')
        kwargs.setdefault('port_bindings', {8500: None})

        super(ConsulDockerRunner, self).__init__(image, name, command, **kwargs)

    @property
    def ready(self):
        """
        Check the service is ready
        """

        try:
            running = self.client.port(self.container, config.DEPENDENCIES[self.service_name.upper()]['PORT'])
        except NotFound:
            return False

        running_host = running[0]['HostIp']
        running_port = running[0]['HostPort']

        consul = Consul(running_host, port=running_port)

        try:
            consul.kv.get('')
            return True
        except ConnectionError:
            return False


class PostgresDockerRunner(DockerRunner):
    """
    Wrapper for redis specific commands
    """

    service_name = 'postgres'

    def __init__(self, image=None, name=None, command=None, **kwargs):

        image = 'postgres' if not image else image
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

        try:
            running = self.client.port(self.container, config.DEPENDENCIES[self.service_name.upper()]['PORT'])
        except NotFound:
            return False

        running_host = running[0]['HostIp']
        running_port = running[0]['HostPort']

        postgres_uri = 'postgresql://postgres:@{host}:{port}'.format(
            host=running_host,
            port=running_port
        )

        try:
            engine = create_engine(postgres_uri)
            engine.connect()
            return True
        except OperationalError as e:
            return False
