"""Conexão com o banco — uma por request, sem estado global mutável.

O código legado mantinha uma única conexão em variável de módulo com
`check_same_thread=False`, compartilhada entre todas as requisições.
"""
import logging
import sqlite3
from contextlib import contextmanager

from flask import current_app, g

from src.database.schema import create_schema, seed_if_empty

logger = logging.getLogger(__name__)


def get_connection():
    """Conexão associada ao contexto da request atual."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_connection(_exception=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


@contextmanager
def transaction(connection):
    """Fronteira transacional explícita: commit no sucesso, rollback em qualquer falha."""
    try:
        connection.execute("BEGIN")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


def init_database(app):
    """Cria o schema e, se configurado, popula os dados de demonstração."""
    with app.app_context():
        connection = get_connection()
        create_schema(connection)
        if app.config.get("SEED_ON_INIT", True):
            if seed_if_empty(connection):
                logger.info("Banco populado com dados de demonstração")
        close_connection()
