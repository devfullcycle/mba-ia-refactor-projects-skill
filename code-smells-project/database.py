"""Camada de conexão: fábrica com escopo por request (via flask.g) + schema + seed.

Substitui o antigo singleton global mutável (`db_connection`) e o `check_same_thread=False`.
"""
import sqlite3

from flask import g
from werkzeug.security import generate_password_hash

from config import settings


def get_db():
    """Retorna a conexão do request atual, criando-a sob demanda (escopo por request)."""
    if "db" not in g:
        g.db = sqlite3.connect(settings.DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    """Fecha a conexão ao fim do request (registrado em teardown_appcontext)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria o schema e semeia dados iniciais. Executar dentro de um app context."""
    db = get_db()
    db.executescript(
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
        );
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha TEXT,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            status TEXT DEFAULT 'pendente',
            total REAL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL
        );
        """
    )
    db.commit()
    _seed(db)


def _seed(db):
    if db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] != 0:
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
    db.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        produtos,
    )

    # Senhas semeadas já com hash (nunca em texto puro).
    usuarios = [
        ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
        ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
        ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
    ]
    db.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        usuarios,
    )
    db.commit()
