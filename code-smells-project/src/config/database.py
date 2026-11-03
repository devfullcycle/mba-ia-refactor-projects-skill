import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)


def get_db():
    """Conexão por contexto de aplicação/request (substitui a conexão global compartilhada)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DB_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def get_readonly_db():
    uri = Path(current_app.config["DB_PATH"]).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_schema():
    db = get_db()
    with db:
        for ddl in SCHEMA:
            db.execute(ddl)


def init_app(app):
    app.teardown_appcontext(close_db)
