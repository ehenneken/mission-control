"""
Provisioners live here
"""
import subprocess
from collections import OrderedDict
import os

from mc.app import create_jinja2
from mc.utils import ChangeDir
from mc.exceptions import UnknownServiceError


class ScriptProvisioner(object):
    """
    Calls a script via subprocess.Popen
    """

    def __init__(self, script, shell):
        self.script = script
        self.shell = shell
        self.process = None
        self.directory = None

    def __call__(self, directory=None, shell=False):
        """
        Creates a Popen process and assigns it to self.process
        :param directory: Directory to cd into
        :param shell
        """
        if directory is None:
            directory = self.directory or '.'

        with ChangeDir(directory):
            self.process = subprocess.Popen(self.script, shell=self.shell)
            self.process.wait()


class PostgresProvisioner(ScriptProvisioner):
    """
    Provisioner for a postgres database.
    """

    _KNOWN_SERVICES = ['adsws', 'metrics', 'biblib']

    def __init__(self, services):
        """
        :param services: iterable of services to provision. Provisioning
            happens in the same order as they are defined
        """
        self.process = None
        self.shell = True
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
                psql_params=self.get_cli_params())

    def get_cli_params(self):
        """
        
        """






