import os

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    # O SQLite só aplica FOREIGN KEYs quando o PRAGMA é ligado em cada conexão.
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()


def init_app(app):
    uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if uri.startswith("sqlite:///") and uri != "sqlite:///:memory:":
        os.makedirs(os.path.dirname(uri[len("sqlite:///"):]) or ".", exist_ok=True)
    db.init_app(app)


def init_schema():
    # Importa os models para registrá-los no metadata antes do create_all.
    from src.models import category, task, user  # noqa: F401

    db.create_all()
