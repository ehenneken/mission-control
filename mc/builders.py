from flask import current_app
from docker import Client
from mc.app import create_jinja2
from mc.exceptions import BuildError
import os
import tarfile
import io


class Builder(object):
    """
    Base builder class
    """
    def __init__(self, commit):
        self.commit = commit
        self.repo = commit.repository
        self.templates = create_jinja2()
        self.tag = "adsabs/{}:{}".format(self.repo, self.commit.commit_hash)
        self.files = []
        self.tarfile = None
        self.built = False
        self.pushed = False

    def build(self):
        """
        Each class should implement their own build method
        """
        raise NotImplementedError


class DockerBuilder(Builder):
    """
    Class responsible for finding the correct templates, rendering them,
    creating a build context, executing docker build, and executing docker push
    """

    def run(self):
        """
        Shortcut method that calls all the methods in the correct order
        to build and push an image
        """
        self.get_templates()
        self.create_docker_context()
        self.build()
        self.push()

    def get_templates(self):
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






