from flask import current_app
from docker import Client
from docker.utils import create_host_config
from mc.app import create_jinja2
from mc.exceptions import BuildError
import os
import logging
import tarfile
import io


class ECSBuilder(object):
    """
    Responsible for building and creating an AWS-ecs deployment
    """

    class DockerContainer(object):
        """
        Represents a docker container as defined in `Dockerrun.aws.json`.
        """

        def __init__(self, build, environment, memory, namespace='adsabs'):
            """
            :param build: mc.models.Build
            :param environment: string environment e.g. "staging"
            :param memory: int memory in MB (100)
            :param namespace: the docker image namespace
            """
            self.build = build
            self.environment = environment
            self.memory = memory
            self.namespace = namespace
            self.name = build.commit.repository

        @property
        def image(self):
            """
            getter for the string formatted docker image as hosted on dockerhub
            """
            return "{}/{}:{}".format(
                self.namespace,
                self.name,
                self.build.commit.commit_hash
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
            self.commit.commit_hash
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
        if "pushing tag" not in line.lower():
            raise BuildError("Failed to push {}: {}".format(self.tag, line))

        self.pushed = True


class DockerRunner(object):
    """
    Responsible for pulling a docker image, creating a container, running
    the container, then tearing down the container
    """

    def __init__(self, image, name, **kwargs):
        """
        :param image: full name of the docker image to pull
        :param name: name of the container in `docker run --name`
        :param mem_limit: Memory limit to enforce on the container
        :param kwargs: keyword args to pass direclty to
            docker.utils.create_host_config
        """
        self.image = image
        self.name = name
        self.host_config = create_host_config(**kwargs)

        self.client = Client(version='auto')
        self.running = None
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

        if callable(callback):
            callback(self.container)

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








