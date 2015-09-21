"""
Test provisioners.py
"""
from mc.provisioners import PostgresProvisioner, ConsulProvisioner
from mc.builders import DockerRunner
from mc.app import create_app

from werkzeug.security import gen_salt
from sqlalchemy import create_engine
import time
import unittest
import requests
import consulate

class TestConsulProvisioner(unittest.TestCase):
    """
    Test the ConsulProvisioner. Use the Docker builder to create the key/value
    store
    """

    def setUp(self):
        """
        Starts a consul node for all the tests
        """
        self.name = 'livetest-consul-{}'.format(gen_salt(5))
        self.builder = DockerRunner(
            image='adsabs/consul:v1.0.0',
            name=self.name,
            mem_limit="50m",
            port_bindings={8500: None},
            command=['-server', '-bootstrap']
        )
        self.builder.start()
        self.port = self.builder.client.port(
            self.builder.container['Id'],
            8500
        )[0]['HostPort']

        # Let consul start
        time.sleep(5)

    def tearDown(self):
        """
        Tears down the consul node used by the tests
        """
        self.builder.teardown()

    def test_provisioning_consul(self):
        """
        Checks that consul is started correctly via docker
        """
        response = requests.get('http://localhost:{}'
                                .format(self.port))
        self.assertEqual(
            response.status_code,
            200,
            msg='Consul service is non-responsive: {}'.format(response.text)
        )

    def _provision(self, service):
        """
        Run the provision for a given service
        """
        app = create_app()
        app.config['DEPENDENCIES']['CONSUL']['PORT'] = self.port
        with app.app_context():
            ConsulProvisioner(service)()

    def test_provisioning_adsws(self):
        """
        First run the provisioner and then we can check that some configuration
        values have been correctly set in the key/value store
        """

        self._provision('adsws')

        consul = consulate.Consul(port=self.port)
        self.assertIn('DEBUG', consul.kv.keys())
        self.assertEqual("false", consul.kv.get('DEBUG'))

class TestPostgresProvisioner(unittest.TestCase):
    """
    Test the PostgresProvisioner. Use the Docker builder to create the database
    """

    def setUp(self):
        self.name = 'livetest-postgres-{}'.format(gen_salt(5))
        self.builder = DockerRunner(
            image='postgres',
            name=self.name,
            mem_limit="50m",
            port_bindings={5432: None},
        )
        self.builder.start()
        self.port = self.builder.client.port(
            self.builder.container['Id'],
            5432
        )[0]['HostPort']

        # Give some seconds for postgres to warm up and become available
        time.sleep(5)

    def tearDown(self):
        self.builder.teardown()

    def _make_db_connection(self, db, user=None):
        """
        retruns a sqlalchemy connection object to a database
        """
        if user is None:
            user = db

        engine = create_engine(
            'postgresql://{user}@localhost:{port}/{db}'.format(
                user=user, port=self.port, db=db
            )
        )
        return engine.connect()

    def _provision(self, service):
        """
        Run the provision for a given service
        """
        # Modifying a live application's config is the most straightforward
        # way to connect to a non-default port for this test case
        app = create_app()
        app.config['DEPENDENCIES']['POSTGRES']['PORT'] = self.port
        with app.app_context():
            PostgresProvisioner(service)()

    def test_provisioning_adsws(self):
        """
        after running the provisioner, make sure that the anon user and
        anon oauth2client exist within the postgres instance
        """

        self._provision('adsws')
        conn = self._make_db_connection('adsws')
        res = conn.execute('SELECT * FROM users').fetchall()
        anon_user = filter(
            lambda i: i['email'] == 'anonymous@ads',
            res,
        )[0]
        self.assertIsNotNone(anon_user)

        res = conn.execute('SELECT * FROM oauth2client').fetchall()
        anon_client = filter(
            lambda i: i['user_id'] == anon_user['id'],
            res,
        )
        self.assertIsNotNone(anon_client)

    def test_provisioning_recommender(self):
        """
        after running the provisioner, make sure that the recommender has the
        expected tables and that they return at least 1 row
        """

        self._provision('recommender')
        conn = self._make_db_connection('recommender')
        coreads = conn.execute('SELECT * FROM coreads').fetchall()
        clusters = conn.execute('SELECT * FROM clusters').fetchall()
        clustering = conn.execute('SELECT * FROM clustering').fetchall()

        self.assertGreater(len(coreads), 0)
        self.assertGreater(len(clusters), 0)
        self.assertGreater(len(clustering), 0)
