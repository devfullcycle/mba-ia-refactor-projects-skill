"""Conexão SQLite por request (sem estado global mutável)."""
import sqlite3
from contextlib import contextmanager

from flask import current_app, g


def _connect(path, read_only=False):
    if read_only:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    else:
        conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """Retorna a conexão do request atual, criando-a sob demanda."""
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE_PATH"])
    return g.db


def get_read_only_db():
    """Conexão somente leitura (usada pelo endpoint administrativo de consulta)."""
    if "db_ro" not in g:
        g.db_ro = _connect(current_app.config["DATABASE_PATH"], read_only=True)
    return g.db_ro


@contextmanager
def transaction():
    """Executa o bloco atomicamente: commit no sucesso, rollback em qualquer erro."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise


def close_db(_exc=None):
    for key in ("db", "db_ro"):
        conn = g.pop(key, None)
        if conn is not None:
            conn.close()


def init_app(app):
    app.teardown_appcontext(close_db)
