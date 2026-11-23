from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Naive UTC 'now' — the SQLite DateTime columns store naive UTC values."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
