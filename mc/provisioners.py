"""
Provisioners live here
"""

import os
import logging
import subprocess

from mc.app import create_jinja2, create_app
from mc.utils import ChangeDir
from mc.exceptions import UnknownServiceError
from flask import current_app
from collections import OrderedDict


class ScriptProvisioner(object):
    """
    Calls a script via subprocess.Popen
    """
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    name = 'provisioner'

    def __init__(self, scripts, shell=False):
        self.scripts = scripts
        self.processes = OrderedDict()
        self.shell = shell
        self.directory = None

        try:
            self.logger = current_app.logger
        except RuntimeError:  # Outside of application context
            self.logger = logging.getLogger("{}-provisioner".format(self.name))
            self.logger.setLevel(logging.DEBUG)

    def __call__(self, directory=None, shell=None, **kwargs):
        """
        Creates a Popen process and assigns it to self.process
        :param directory: Directory to cd into
        :param shell: kwarg passed to subprocess.Popen
        """
        self.logger.debug('Running subprocess')

        if directory is None:
            directory = self.directory or '.'

        if shell is None:
            shell = self.shell

        with ChangeDir(directory):
            scripts = list(self.scripts)
            while scripts:
                script = scripts.pop()
                p = subprocess.Popen(script, shell=shell)
                p.wait()
                self.processes["{}".format(script)] = p


class PostgresProvisioner(ScriptProvisioner):
    """
    Provisioner for a postgres database.
    """

    # TODO: This should be based on what templates are discoverable, not
    # hard coded!
    _KNOWN_SERVICES = ['adsws', 'metrics', 'biblib', 'graphics', 'recommender']
    name = 'postgres'

    def __init__(self, services, **kwargs):
        """
        :param services: iterable of services to provision. Provisioning
            happens in the same order as they are defined
        """
        super(PostgresProvisioner, self).__init__(scripts=None, shell=True)

        self.processes = OrderedDict()
        services = [services] if isinstance(services, basestring) else services

        if set(services).difference(self._KNOWN_SERVICES):
            raise UnknownServiceError(
                "{}".format(
                    set(services).difference(self._KNOWN_SERVICES)))

        self.services = OrderedDict()
        engine = create_jinja2()
        template = engine.get_template('postgres/base.psql.template')
        self.directory = os.path.dirname(template.filename)
        for s in services:
            self.services[s] = template.render(
                database=s,
                user=s,
                psql_args='--username postgres --port {} --host {}'
                .format(
                    kwargs['container'].running_port,
                    kwargs['container'].running_host
                )
            )
        self.scripts = self.services.values()

    @staticmethod
    def get_cli_params():
        """
        finds the command line parameters necessary to pass to `psql`
        :returns string containing psql-specifically formatted params
        """
        try:
            config = current_app.config
        except RuntimeError:  # Outside of application context
            config = create_app().config
        config = config['DEPENDENCIES']['POSTGRES']

        cli = "--username {username} --port {port} --host {host}".format(
            username=config.get('USERNAME', 'postgres'),
            port=config.get('PORT', 5432),
            host=config.get('HOST', 'localhost'),
        )

        return cli


class ConsulProvisioner(ScriptProvisioner):
    """
    Provision the consul cluster key-value store
    """

    name = 'consul'

    def __init__(self, services, **kwargs):

        super(ConsulProvisioner, self).__init__(scripts=None, shell=True)

        self._KNOWN_SERVICES = self.known_services()
        self.processes = OrderedDict()

        services = [services] if isinstance(services, basestring) else services
        if set(services).difference(self._KNOWN_SERVICES):
            raise UnknownServiceError(
                "{}".format(
                    set(services).difference(self._KNOWN_SERVICES)))

        self.services = OrderedDict()
        engine = create_jinja2()
        template = engine.get_template('{}/base.consul.template'.format(self.name))
        self.directory = os.path.dirname(template.filename)
        for s in services:
            self.services[s] = template.render(
                service=s,
                port=kwargs['container'].running_port,
                db_host=ConsulProvisioner.get_db_params()['HOST'],
                db_port=ConsulProvisioner.get_db_params()['PORT']
            )
        self.scripts = self.services.values()

    @classmethod
    def known_services(cls):
        """
        Services consul knows about
        :return: list of services
        """
        template_dir = '{base}/{provisioner}'.format(
            base=cls.template_dir,
            provisioner=cls.name
        )
        return [_dir for _dir in os.listdir(template_dir)
                if os.path.isdir(os.path.join(template_dir, _dir))]

    @staticmethod
    def get_cli_params():
        """
        finds the command line parameters necessary to pass to `psql`
        :returns string containing psql-specifically formatted params
        """
        try:
            config = current_app.config
        except RuntimeError:  # Outside of application context
            config = create_app().config
        config = config['DEPENDENCIES']['CONSUL']

        cli = "{port}".format(
            port=config.get('PORT', 8500),
        )

        return cli

    @staticmethod
    def get_db_params():
        """
        finds the parameters necessary to connect to the postgres instance.
        :return: string uri of the postgres instance
        """
        try:
            config = current_app.config
        except RuntimeError:  # Outside of application context
            config = create_app().config

        return config['DEPENDENCIES']['POSTGRES']
