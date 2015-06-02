"""
Database models
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()