"""
test manage.py commands
"""

from flask.ext.testing import TestCase
from mc.app import create_app
from mc.tests.stubdata import github_commit_payload
from mc.manage import BuildDockerImage, MakeDockerrunTemplate, ECSDeploy
from mc.models import db, Commit, Build
import mock
import httpretty
from sqlalchemy.orm.exc import NoResultFound
import json


class TestECSDeploy(TestCase):
    """
    Test the manage.py deploy command
    """
    def create_app(self):
        return create_app()

    @mock.patch('mc.manage.register_task_revision')
    def test_run(self, mocked):
        """
        manage.py -t "<json>" should be passed to tasks.register_task_revision
        """
        ECSDeploy().run(task_definition='{"valid": "json"}', app=self.app)
        mocked.assert_called_with('{"valid": "json"}')


class TestMakeDockerrunTemplate(TestCase):
    """
    Test the manage.py render_dockerrun command
    """

    def create_app(self):
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"
        return app

    def setUp(self):
        db.create_all()
        self.commit = Commit(
            commit_hash='master',
            repository="adsws"
        )
        self.build = Build(commit=self.commit)

        # Add some unrelated commit/builds to ensure that these are *not*
        # rendered
        c = Commit(commit_hash="_hash_", repository="_repo_")
        b = Build(commit=c)

        db.session.add(self.commit)
        db.session.add(self.build)
        db.session.add(c)
        db.session.add(b)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_run(self):
        """
        manage.py render_dockerrun -c repo:hash env mem return a rendered
        Dockerrun.aws.json
        """
        containers = [
            ["adsws:master", "staging", 100],
            ["adsws:master", "production", 150],
        ]
        r = MakeDockerrunTemplate().run(
            containers=containers, app=self.app, family="unittest-family"
        )
        self.assertNotIn("_hash_", r)
        self.assertNotIn("_repo_", r)
        r = json.loads(r)
        self.assertEqual("unittest-family", r['family'])
        self.assertEqual("adsabs/adsws:master", r['containerDefinitions'][0]["image"])
        self.assertEqual("adsabs/adsws:master", r['containerDefinitions'][1]["image"])
        self.assertEqual(100, r['containerDefinitions'][0]["memory"])
        self.assertEqual(150, r['containerDefinitions'][1]["memory"])
        containers = [
            ["adsws:doesnt_exist", "staging", 100],
        ]
        with self.assertRaises(NoResultFound):
            MakeDockerrunTemplate().run(
                containers=containers, app=self.app, family="unittest-family"
            )



class TestBuildDockerImage(TestCase):
    """
    Test the manage.py build command
    """

    def create_app(self):
        app = create_app()
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"
        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @httpretty.activate
    def test_run(self):
        """
        manage.py build <repo> <commit> should create a new Commit and
        build_docker.delay() should be called
        """
        repo, commit = "unittest-repo", "unittest-hash"

        httpretty.register_uri(
            httpretty.GET,
            self.app.config['GITHUB_COMMIT_API'].format(
                repo=repo, hash=commit
            ),
            body=github_commit_payload.payload,
            content_type="application/json"
        )

        with mock.patch('mc.manage.build_docker') as mocked:
            BuildDockerImage().run(repo, commit, app=self.app)
            c = db.session.query(Commit).filter_by(
                repository=repo, commit_hash=commit
            ).one()
            self.assertIsNotNone(c)
            mocked.delay.assert_called_once_with(c.id)
            BuildDockerImage().run(repo, commit, app=self.app)
            c2 = db.session.query(Commit).filter_by(
                repository=repo, commit_hash=commit
            ).one()
            self.assertEqual(c.id, c2.id)



