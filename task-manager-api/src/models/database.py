"""Database instance and shared persistence helpers."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Current UTC time as a naive datetime (the format stored in the SQLite columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
