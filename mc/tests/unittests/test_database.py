from flask.ext.testing import TestCase
from mc.app import create_app
from mc.models import db, Commit, Build
import datetime
from dateutil.tz import tzlocal
from sqlalchemy.exc import IntegrityError


class TestModels(TestCase):
    """
    Test flask-sqlalchemy database operations
    """
    def create_app(self):
        """
        Called once at the beginning of the tests; must return the application
        instance
        :return: flask.Flask application instance
        """
        _app = create_app()
        # Override whatever database uri is in the config for tests;
        # Use an in-memory sqlite database to ensure that no production data
        # are touched
        _app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite://"
        _app.config['MC_LOGGING'] = {}
        return _app

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

    def test_commit_model(self):
        """
        CRUD on models.Commit
        """

        # Create
        commit = Commit(
            commit_hash='test-hash',
            timestamp=datetime.datetime(2015, 6, 3, 12, 26, 57, tzinfo=tzlocal()),
            repository="test-repo",
            message="test-message",
        )
        db.session.add(commit)
        db.session.commit()

        # commit_hash should be unique
        _ = Commit(commit_hash='test-hash')
        with self.assertRaises(IntegrityError):
            db.session.add(_)
            db.session.commit()
        db.session.remove()

        # Read
        c = Commit.query.first()
        self.assertEqual(c.commit_hash, 'test-hash')
        self.assertEqual(
            c.timestamp,
            datetime.datetime(2015, 6, 3, 12, 26, 57)
        )

        # Update
        c.commit_hash = 'mutated'
        db.session.commit()
        self.assertEqual(Commit.query.first().commit_hash, 'mutated')

        # Delete
        c = Commit.query.first()
        db.session.delete(c)
        db.session.commit()
        self.assertIsNone(Commit.query.first())

    def test_build_model(self):
        """
        CRUD on models.Build
        """

        # Create
        commit = Commit(commit_hash='test-hash')
        db.session.add(commit)
        build = Build(commit=commit, built=False, pushed=False)
        db.session.commit()

        # Read
        b = build.query.first()
        self.assertEqual(b, build)
        self.assertEqual(b.commit, commit)

        # Update
        b.no_cache = True
        b.commit = Commit(commit_hash='mutated')
        db.session.commit()
        self.assertEqual(Build.query.first().no_cache, True)
        self.assertEqual(Build.query.first().commit.commit_hash, 'mutated')

        # Delete
        b = Build.query.first()
        db.session.delete(b)
        db.session.commit()
        self.assertIsNone(Build.query.first())

