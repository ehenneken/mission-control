"""
Test utilities
"""
from flask.ext.testing import TestCase
from mock import patch
from mc import app
from mc.models import db, Commit, Build
from mc.tasks import register_task_revision, build_docker, update_service, run_task
import datetime


class TestRegisterTaskDefinition(TestCase):
    """
    Test the register_task_definition task
    """
    def create_app(self):
        return app.create_app()

    @patch('mc.tasks.get_boto_session')
    def test_register_task_definition(self, Session):
        """
        the register_task_definition task should pass a dockerrun.aws.json
        template as kwargs to boto3.ecs.register_task_definition
        """
        session = Session.return_value
        client = session.client.return_value

        with patch('mc.builders.ECSBuilder') as ECSBuilder:
            ecsbuild = ECSBuilder.return_value
            ecsbuild.render_template.return_value = '''{
                "family": "unittest-family",
                "containerDefinitions": [],
                "volumes": []
            }'''
            register_task_revision(ecsbuild)

        session.client.assert_called_with('ecs')
        client.register_task_definition.assert_called_with(
            family="unittest-family",
            containerDefinitions=[],
            volumes=[],
        )
        register_task_revision('{"valid": "json"}')
        client.register_task_definition.assert_called_with(valid="json")


class TestUpdateService(TestCase):
    """
    Test the update service task
    """
    def create_app(self):
        return app.create_app()

    @patch('mc.tasks.get_boto_session')
    def test_update_service(self, Session):
        """
        the update_service task should pass call the boto3 task after
        establishing a session
        """
        session = Session.return_value
        client = session.client.return_value
        kwargs = dict(
            cluster="unittest-cluster",
            service="unittest-service",
            desiredCount=5,
            taskDefinition='{"valid": "json"}',
        )
        update_service(**kwargs)
        session.client.assert_called_with('ecs')
        client.update_service.assert_called_with(**kwargs)

class TestRunTask(TestCase):
    """
    Test the run task
    """
    def create_app(self):
        return app.create_app()

    @patch('mc.tasks.get_boto_session')
    def test_run_task(self, Session):
        """
        the run_task task should pass call the boto3 task after
        establishing a session
        """
        session = Session.return_value
        client = session.client.return_value
        kwargs = dict(
            cluster="unittest-cluster",
            desiredCount=1,
            taskDefinition='{"valid": "json"}',
        )
        run_task(**kwargs)
        session.client.assert_called_with('ecs')
        client.run_task.assert_called_with(**kwargs)

class TestDockerBuildTask(TestCase):
    """
    Test the Build task
    """
    def create_app(self):
        app_ = app.create_app()
        app_.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        app_.config['MC_LOGGING'] = {}
        return app_

    def setUp(self):
        """
        setUp and tearDown are run at the start of each test; ensure
        that a fresh database is used for each test.
        """
        db.create_all()

    def tearDown(self):
        """
        setUp and tearDown are run at the start of each test; ensure
        that a fresh database is used for each test.
        """
        db.session.remove()
        db.drop_all()

    @patch('mc.builders.Client')
    def test_docker_build_task(self, mocked):
        """
        Tests that the docker_build_task adds a Build entry. Assumes the
        underlying builder.run command does not Raise
        """
        commit = Commit(
            repository='adsws',
            commit_hash='test-hash',
        )
        db.session.add(commit)
        db.session.commit()
        commit_id = commit.id

        instance = mocked.return_value
        instance.build.return_value = ['Successfully built']
        instance.push.return_value = ['pushing tag']

        build_docker(commit_id)

        build = db.session.query(Build).first()
        self.assertEqual(build.commit_id, commit_id)
        self.assertAlmostEqual(
            build.timestamp,
            datetime.datetime.now(),
            delta=datetime.timedelta(seconds=1)
        )
        self.assertTrue(build.built)
        self.assertTrue(build.pushed)