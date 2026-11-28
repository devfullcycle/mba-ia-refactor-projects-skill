"""Database instance, clock helper and the shared repository base."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Naive UTC 'now' — the SQLite DateTime columns store naive UTC values."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseRepository:
    """Session operations shared by every repository (one unit of work per request)."""

    model = None  # set by each concrete repository

    def __init__(self, database):
        self._db = database

    @property
    def session(self):
        return self._db.session

    def get(self, entity_id):
        return self.session.get(self.model, entity_id)

    def new(self, **fields):
        """Builds an entity from validated fields and adds it to the unit of work (not committed)."""
        entity = self.model(**fields)
        self.session.add(entity)
        return entity

    def add(self, entity):
        self.session.add(entity)

    def delete(self, entity):
        self.session.delete(entity)

    def commit(self):
        self.session.commit()
