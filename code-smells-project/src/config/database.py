import logging
import sqlite3
from pathlib import Path

from flask import current_app, g

logger = logging.getLogger(__name__)

# Bancos novos já nascem com restrições de integridade.
SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL CHECK (preco >= 0),
        estoque INTEGER NOT NULL CHECK (estoque >= 0),
        categoria TEXT,
        ativo INTEGER NOT NULL DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        senha TEXT NOT NULL,
        tipo TEXT NOT NULL DEFAULT 'cliente' CHECK (tipo IN ('cliente', 'admin')),
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL REFERENCES usuarios (id),
        status TEXT NOT NULL DEFAULT 'pendente',
        total REAL NOT NULL CHECK (total >= 0),
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER NOT NULL REFERENCES pedidos (id) ON DELETE CASCADE,
        produto_id INTEGER NOT NULL REFERENCES produtos (id),
        quantidade INTEGER NOT NULL CHECK (quantidade > 0),
        preco_unitario REAL NOT NULL
    )
    """,
)

# Migrações aplicáveis também a bancos criados pela versão anterior (sem constraints na tabela).
MIGRACOES = (
    ("e-mail único", "CREATE UNIQUE INDEX IF NOT EXISTS ux_usuarios_email ON usuarios (email COLLATE NOCASE)"),
    ("índice de pedidos por usuário", "CREATE INDEX IF NOT EXISTS ix_pedidos_usuario ON pedidos (usuario_id)"),
    ("índice de itens por pedido", "CREATE INDEX IF NOT EXISTS ix_itens_pedido ON itens_pedido (pedido_id)"),
)


def _conectar(alvo, **kwargs):
    conn = sqlite3.connect(alvo, **kwargs)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    """Conexão por contexto de aplicação/request."""
    if "db" not in g:
        g.db = _conectar(current_app.config["DB_PATH"])
    return g.db


def get_readonly_db():
    uri = Path(current_app.config["DB_PATH"]).resolve().as_uri() + "?mode=ro"
    return _conectar(uri, uri=True)


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_schema():
    db = get_db()
    with db:
        for ddl in SCHEMA:
            db.execute(ddl)

    for descricao, ddl in MIGRACOES:
        try:
            with db:
                db.execute(ddl)
        except sqlite3.IntegrityError:
            logger.error("Migração '%s' não aplicada: existem dados duplicados a corrigir manualmente.", descricao)


def init_app(app):
    app.teardown_appcontext(close_db)
