"""
Database models
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Commit(db.Model):
    """
    Represents a git commit
    """
    id = Column(Integer, primary_key=True)
    commit_hash = Column(String, unique=True)
    message = Column(String)
    timestamp = Column(DateTime)
    author = Column(String)
    repository = Column(String)


class Build(db.Model):
    """
    Represents a docker build
    """
    id = Column(Integer, primary_key=True)
    commit_id = Column(Integer, ForeignKey('commit.id'))
    commit = db.relationship(
        'Commit',
        backref=db.backref('builds', lazy='dynamic')
    )
    timestamp = Column(DateTime)
    built = Column(Boolean)
    pushed = Column(Boolean)


class DockerContainer(object):
    """
    Represents a docker container as defined by `Dockerrun.aws.json`.
    This is not a database-backed model; it is in-app only
    """

    def __init__(self, build, environment, memory):
        """
        :param build:
        :param environment:
        :param memory:
        """

        self.build = build
        self.environment = environment
        self.memory = memory