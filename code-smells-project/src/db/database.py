"""SQLite connection lifecycle, schema and seed data."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from flask import Flask, g
from werkzeug.security import generate_password_hash

from src.config.settings import Settings, load_settings

logger = logging.getLogger(__name__)


def get_settings() -> Settings:
    return getattr(g, "_settings", None) or load_settings()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        settings = get_settings()
        conn = sqlite3.connect(settings.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db  # type: ignore[return-value]


def close_db(_: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app: Flask, settings: Settings) -> None:
    app.teardown_appcontext(close_db)

    @app.before_request
    def _attach_settings() -> None:
        g._settings = settings


def _create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pendente',
            total REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );

        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        );
        """
    )


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    if count > 0:
        return

    produtos = [
        ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
        ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
        ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
        ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
        ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
        ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
        ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
        ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
        ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
        ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
    ]
    conn.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
        "VALUES (?, ?, ?, ?, ?)",
        produtos,
    )

    usuarios = [
        ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
        ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
        ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
    ]
    conn.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        usuarios,
    )
    conn.commit()
    logger.info("Database seeded with sample products and users")


def _migrate_plaintext_passwords(conn: sqlite3.Connection) -> None:
    """Hash legacy plaintext passwords from the pre-refactor database."""
    rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    updated = 0
    for row in rows:
        senha = row["senha"] or ""
        if senha.startswith(("pbkdf2:", "scrypt:", "argon2:")):
            continue
        conn.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (generate_password_hash(senha), row["id"]),
        )
        updated += 1
    if updated:
        conn.commit()
        logger.info("Migrated %s plaintext password(s) to hashes", updated)


def init_db(settings: Settings | None = None) -> None:
    settings = settings or load_settings()
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        _create_schema(conn)
        _seed_if_empty(conn)
        _migrate_plaintext_passwords(conn)
        conn.commit()
    finally:
        conn.close()


def reset_all_data(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM itens_pedido")
    conn.execute("DELETE FROM pedidos")
    conn.execute("DELETE FROM produtos")
    conn.execute("DELETE FROM usuarios")
    conn.commit()
    _seed_if_empty(conn)
