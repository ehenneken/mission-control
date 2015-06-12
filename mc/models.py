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