from pathlib import Path
import sqlite3

from flask import current_app, g

from security import hash_password


def _connect(database_path: str) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE"])
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialize_database(database_path: str) -> None:
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)

    connection = _connect(database_path)
    try:
        _create_schema(connection)
        _seed_data(connection)
        _migrate_plaintext_passwords(connection)
        connection.commit()
    finally:
        connection.close()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL DEFAULT '',
            preco REAL NOT NULL,
            estoque INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            total REAL NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
        """
    )


def _seed_data(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] > 0:
        return

    produtos = [
        ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
        ("Mouse Wireless", "Mouse sem fio ergonomico", 89.90, 50, "informatica"),
        ("Teclado Mecanico", "Teclado mecanico RGB", 299.90, 30, "informatica"),
        ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
        ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
        ("Cadeira Gamer", "Cadeira ergonomica", 1299.90, 8, "moveis"),
        ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
        ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
        ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
        ("Camiseta Dev", "Camiseta estampa codigo", 59.90, 100, "vestuario"),
    ]
    cursor.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        produtos,
    )

    usuarios = [
        ("Admin", "admin@loja.com", hash_password("admin123"), "admin"),
        ("Joao Silva", "joao@email.com", hash_password("123456"), "cliente"),
        ("Maria Santos", "maria@email.com", hash_password("senha123"), "cliente"),
    ]
    cursor.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        usuarios,
    )


def _migrate_plaintext_passwords(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute("SELECT id, senha FROM usuarios")
    rows = cursor.fetchall()
    for row in rows:
        senha = row["senha"] or ""
        if senha.startswith("pbkdf2_sha256$"):
            continue
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (hash_password(senha), row["id"]),
        )
