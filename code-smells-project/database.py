"""Conexão e inicialização do banco de dados SQLite.

A conexão é criada de forma preguiçosa (lazy) via getter, eliminando o
estado global mutável e permitindo um único ponto de acesso à persistência.
"""

import sqlite3
import hashlib
from config import settings

_db_connection = None


def _senha_hash(senha):
    """Hash consistente com models/usuario_model (SHA-256 de demonstração)."""
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def get_db():
    """Retorna a conexão única do módulo, criada sob demanda."""
    global _db_connection
    if _db_connection is None:
        _db_connection = sqlite3.connect(settings.DB_PATH, check_same_thread=False)
        _db_connection.row_factory = sqlite3.Row
        _init_schema(_db_connection)
        _seed_default_data(_db_connection)
    return _db_connection


def _init_schema(conn):
    cursor = conn.cursor()
    cursor.executescript(
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
    conn.commit()


def _seed_default_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] == 0:
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
        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            produtos,
        )

        usuarios = [
            ("Admin", "admin@loja.com", _senha_hash("admin123"), "admin"),
            ("João Silva", "joao@email.com", _senha_hash("123456"), "cliente"),
            ("Maria Santos", "maria@email.com", _senha_hash("senha123"), "cliente"),
        ]
        cursor.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            usuarios,
        )
        conn.commit()