"""
test manage.py commands
"""

from flask.ext.testing import TestCase
from mc.app import create_app
from mc.tests.stubdata import github_commit_payload
from mc.manage import BuildDockerImage, MakeDockerrunTemplate, \
    RegisterTaskRevision, UpdateService, ManageTestCluster
from mc.models import db, Commit, Build
import mock
import httpretty
from sqlalchemy.orm.exc import NoResultFound
import json


class TestManageTestCluster(TestCase):
    """
    Test the manage.py test_cluster command
    """
    def create_app(self):
        return create_app()

    @mock.patch('mc.manage.start_test_environment')
    def test_start_request(self, mocked):
        """
        Test starting the cluster
        """
        ManageTestCluster().run(
            command='start',
            test_id=None
        )
        mocked.assert_called_with(test_id=None)

    @mock.patch('mc.manage.stop_test_environment')
    def test_stop_request(self, mocked):
        """
        Test starting the cluster
        """
        ManageTestCluster().run(
            command='stop',
            test_id=None
        )
        mocked.assert_called_with(test_id=None)

    @mock.patch('mc.manage.run_ci_test')
    def test_stop_request(self, mocked):
        """
        Test starting the cluster
        """
        ManageTestCluster().run(
            command='run',
            test_id=None
        )
        mocked.assert_called_with(test_id=None)


class TestRegisterTaskRevision(TestCase):
    """
    Test the manage.py register_task_revision command
    """
    def create_app(self):
        return create_app()

    @mock.patch('mc.manage.register_task_revision')
    def test_run(self, mocked):
        """
        manage.py -t "<json>" should be passed to tasks.register_task_revision
        """
        RegisterTaskRevision().run(
            task_definition='{"valid": "json"}', app=self.app
        )
        mocked.assert_called_with('{"valid": "json"}')


class TestUpdateService(TestCase):
    """
    Test the manage.py update_service command
    """
    def create_app(self):
        return create_app()

    @mock.patch('mc.manage.update_service')
    def test_run(self, mocked):
        """
        manage.py update_service <args> should be passed to tasks.update_service
        """
        kwargs = dict(
            cluster="unittest-cluster",
            service="unittest-service",
            desiredCount=1,
            taskDefinition="unittest-taskdefinition",
        )
        UpdateService().run(app=self.app, **kwargs)
        mocked.assert_called_with(**kwargs)


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

        # Tags
        self.commit.tag = 'tag'
        db.session.add(self.commit)
        db.session.commit()
        containers = [
            ["adsws:tag", "staging", 100]
        ]
        r = MakeDockerrunTemplate().run(
            containers=containers, app=self.app, family="unittest-family"
        )
        self.assertNotIn("_hash_", r)
        self.assertNotIn("_repo_", r)
        r = json.loads(r)
        self.assertEqual("adsabs/adsws:tag", r['containerDefinitions'][0]["image"])


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
        manage.py build -r <repo> -c <commit> should create a new Commit and
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

    @httpretty.activate
    def test_run_tag(self):
        """
        manage.py build -r <repo> -t <tag> should create a new Commit and
        build_docker.delay() should be called
        """
        repo, tag, commit = 'unittest-repo', 'unittest-tag', 'unittest-commit'

        tag, tag_commit, no_tag = 'unittest-tag', 'unnitest-tag-commit', \
                                  'no-tag'

        httpretty.register_uri(
            httpretty.GET,
            self.app.config['GITHUB_TAG_FIND_API'].format(
                repo=repo, tag=tag
            ),
            body=github_commit_payload.payload_tag,
            content_type='application/json'
        )

        httpretty.register_uri(
            httpretty.GET,
            self.app.config['GITHUB_TAG_GET_API'].format(
                repo=repo, hash=tag_commit
            ),
            body=github_commit_payload.payload_get_tag,
            content_type='application/json'
        )

        httpretty.register_uri(
            httpretty.GET,
            self.app.config['GITHUB_TAG_FIND_API'].format(
                repo=repo, tag=no_tag
            ),
            body=github_commit_payload.payload_tag_fail,
            content_type='application/json'
        )

        httpretty.register_uri(
            httpretty.GET,
            self.app.config['GITHUB_COMMIT_API'].format(
                repo=repo, hash=commit
            ),
            body=github_commit_payload.payload,
            content_type='application/json'
        )

        with mock.patch('mc.manage.build_docker') as mocked:

            BuildDockerImage().run(repo, commit_hash=commit, app=self.app)
            c = db.session.query(Commit).filter_by(
                repository=repo, commit_hash=commit
            ).one()
            self.assertIsNotNone(c)
            mocked.delay.assert_called_once_with(c.id)

            BuildDockerImage().run(repo, tag=tag, app=self.app)
            c1 = db.session.query(Commit).filter_by(
                repository=repo, tag=tag
            ).one()
            self.assertEqual(c.id, c1.id)

            BuildDockerImage().run(repo, tag=tag, app=self.app)
            c2 = db.session.query(Commit).filter_by(
                repository=repo, tag=tag
            ).one()
            self.assertEqual(c.id, c2.id)

            c3 = db.session.query(Commit).filter_by(
                repository=repo, commit_hash=commit
            ).one()
            self.assertEqual(c.id, c3.id)

            with self.assertRaises(KeyError):
                BuildDockerImage().run(repo, tag=no_tag, app=self.app)
