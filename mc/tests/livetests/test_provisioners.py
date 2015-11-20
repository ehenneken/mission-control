"""
Test provisioners.py
"""
from mc.provisioners import PostgresProvisioner, ConsulProvisioner, TestProvisioner, SolrProvisioner
from mc.builders import DockerRunner, ConsulDockerRunner, PostgresDockerRunner, \
        GunicornDockerRunner, SolrDockerRunner

from jinja2 import Template
from werkzeug.security import gen_salt
from sqlalchemy import create_engine

import json
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
        self.builder = ConsulDockerRunner(
            name=self.name,
        )

        self.builder.start()
        self.port = self.builder.client.port(
            self.builder.container['Id'],
            8500
        )[0]['HostPort']

    def tearDown(self):
        """
        Tears down the consul node used by the tests
        """
        self.builder.teardown()

    def test_running_consul(self):
        """
        Checks that consul is started correctly via docker
        """

        while True:
            response = requests.get('http://localhost:{}/v1/kv/health'
                                    .format(self.port))
            if response.status_code == 404:
                break

        self.assertEqual(
            response.status_code,
            404,
            msg='Consul service is non-responsive: {}'.format(response.text)
        )

    def _provision(self, service):
        """
        Run the provision for a given service
        """
        ConsulProvisioner(service, container=self.builder)()

    def test_provisioning_adsws_service(self):
        """
        First run the provisioner and then we can check that some configuration
        values have been correctly set in the key/value store
        """
        self._provision('adsws')

        # Obtain what we expect to find
        config_file = '{}/{}/adsws/adsws.config.json'.format(
            ConsulProvisioner.template_dir,
            ConsulProvisioner.name,
        )

        with open(config_file) as json_file:
            template = Template(json_file.read())

        json_config = template.render(
            db_host='localhost',
            db_port=5432,
            cache_host='localhost',
            cache_port=6379
        )

        config = json.loads(json_config)

        # Compare with consul
        consul = consulate.Consul(port=self.port)
        for key in config:

            self.assertIn(key, consul.kv.keys())
            self.assertEqual(
                config[key],
                consul.kv.get(key),
                msg='Key {} mismatch: {} != {}'.format(
                    key,
                    config[key],
                    consul.kv.get(key)
                )
            )

        cache = consul.kv.get('config/adsws/staging/CACHE')
        self.assertIn(
            'localhost',
            cache,
        )
        self.assertIn(
            '6379',
            cache,
        )

        db_uri = consul.kv.get('config/adsws/staging/SQLALCHEMY_DATABASE_URI')
        self.assertEqual(
            db_uri,
            '"postgresql+psycopg2://postgres:@localhost:5432/adsws"',
            msg='Provisioning is not working: {} != '
                'postgresql+psycopg2://postgres:@localhost:5432/adsws'.format(db_uri)
        )


class TestPostgresProvisioner(unittest.TestCase):
    """
    Test the PostgresProvisioner. Use the Docker builder to create the database
    """

    def setUp(self):
        self.name = 'livetest-postgres-{}'.format(gen_salt(5))
        self.builder = PostgresDockerRunner(
            name=self.name,
        )
        self.builder.start()
        self.port = self.builder.client.port(
            self.builder.container['Id'],
            5432
        )[0]['HostPort']

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

        PostgresProvisioner(service, container=self.builder)()

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


class TestTestProvisioner(unittest.TestCase):
    """
    Test the provisioning of the test cluster script
    """

    def setUp(self):
        """
        Setup the tests
        """
        self.name = 'livetest-adsws-pythonsimpleserver-{}'.format(gen_salt(5))
        self.builder = GunicornDockerRunner(
            image='adsabs/pythonsimpleserver:v1.0.0',
            name=self.name,
        )
        self.builder.start()
        info = self.builder.client.port(
            self.builder.container['Id'],
            80
        )[0]
        self.host = info['HostIp']
        self.port = info['HostPort']

    def tearDown(self):
        """
        Teardown the tests
        """
        self.builder.teardown()

    def test_that_the_script_file_is_provisioned(self):
        """
        Tests that the script file is provisioned as we expect it to be
        """
        test_provisioner = TestProvisioner(services=['adsrex'])

        api_url = 'API_URL="http://{host}:{port}"'.format(
            host=self.host,
            port=self.port
        )
        self.assertIn(api_url, test_provisioner.scripts[0])


class TestSolrProvisioner(unittest.TestCase):
    """
    Test the SolrProvisioner. Use the Docker builder to create the index
    """

    def setUp(self):
        """
        Starts a solr node for all the tests
        """
        self.name = 'livetest-solr-{}'.format(gen_salt(5))
        self.builder = SolrDockerRunner(
            name=self.name,
        )

        self.builder.start()
        self.port = self.builder.client.port(
            self.builder.container['Id'],
            8983
        )[0]['HostPort']

    def tearDown(self):
        """
        Tears down the consul node used by the tests
        """
        self.builder.teardown()

    def _provision(self, service):
        """
        Run the provision for a given service
        """
        SolrProvisioner(service, container=self.builder)()

    def test_provisioning_recommender_service(self):
        """
        First run the provisioner and then we can check that the documents have been added to the solr index
        """
        self._provision('recommender')

        # Obtain what we expect to find
        config_file = '{}/{}/recommender/recommender.json'.format(
            SolrProvisioner.template_dir,
            SolrProvisioner.name,
        )

        with open(config_file) as json_file:
            config = json.load(json_file)

        # Compare with consul
        for document in config:
            response = requests.get('http://{host}:{port}/solr/query?q=bibcode:{bibcode}'.format(
                host='localhost',
                port=self.port,
                bibcode=document['bibcode'])
            )
            self.assertEqual(
                200,
                response.status_code,
                msg='We expect a 200 response but got: {}, {}'.format(response.status_code, response.json())
            )

            actual_document = response.json()['response']['docs'][0]

            # Not all key/values are returned in the same fashion, so the following specified are some hand-picked
            # keywords that we want to test were entered correctly into Solr
            known_keys = ['pubdate', 'first_author', 'abstract', 'read_count', 'doctype', 'year', 'bibcode', 'volume']

            for key in known_keys:
                self.assertIn(
                    key,
                    actual_document.keys(),
                    msg='Could not find key "{}" in response: {}'.format(key, actual_document.keys())
                )
                self.assertEqual(
                    document[key],
                    actual_document[key],
                    msg='Key "{}" mismatch: expected "{}" != actual "{}"'.format(
                        key,
                        document[key],
                        actual_document[key]
                    )
                )
