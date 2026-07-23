"""SQLite connection lifecycle, schema and transaction boundaries."""

from __future__ import annotations

from contextlib import contextmanager
import sqlite3
import threading
from collections.abc import Iterator

from store.infrastructure.security import PasswordHasher


PRODUCT_SEED = [
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


class SQLiteDatabase:
    def __init__(self, path: str):
        self.path = path
        self._initialized = False
        self._initialization_lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def connect(self) -> sqlite3.Connection:
        connection = self._connect()
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 10000")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(
        self,
        hasher: PasswordHasher | None = None,
        bootstrap_email: str | None = None,
        bootstrap_password: str | None = None,
    ) -> None:
        if self._initialized:
            return
        with self._initialization_lock:
            if self._initialized:
                return
            hasher = hasher or PasswordHasher()
            with self.connection() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS produtos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL CHECK (length(nome) BETWEEN 2 AND 200),
                        descricao TEXT NOT NULL DEFAULT '',
                        preco REAL NOT NULL CHECK (preco >= 0),
                        estoque INTEGER NOT NULL CHECK (estoque >= 0),
                        categoria TEXT NOT NULL CHECK (categoria IN ('informatica','moveis','vestuario','geral','eletronicos','livros')),
                        ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
                        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                        senha TEXT NOT NULL,
                        tipo TEXT NOT NULL DEFAULT 'cliente' CHECK (tipo IN ('cliente', 'admin')),
                        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS pedidos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
                        status TEXT NOT NULL DEFAULT 'pendente' CHECK (status IN ('pendente','aprovado','enviado','entregue','cancelado')),
                        total REAL NOT NULL CHECK (total >= 0),
                        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS itens_pedido (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pedido_id INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
                        produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE RESTRICT,
                        quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                        preco_unitario REAL NOT NULL CHECK (preco_unitario >= 0)
                    );
                    CREATE UNIQUE INDEX IF NOT EXISTS usuarios_email_unique ON usuarios(email COLLATE NOCASE);

                    CREATE TRIGGER IF NOT EXISTS produtos_validate_insert
                    BEFORE INSERT ON produtos
                    WHEN NEW.nome IS NULL OR length(NEW.nome) NOT BETWEEN 2 AND 200 OR NEW.preco IS NULL OR NEW.preco < 0 OR NEW.estoque IS NULL OR NEW.estoque < 0 OR NEW.categoria NOT IN ('informatica','moveis','vestuario','geral','eletronicos','livros')
                    BEGIN SELECT RAISE(ABORT, 'produto inválido'); END;
                    CREATE TRIGGER IF NOT EXISTS produtos_validate_update
                    BEFORE UPDATE ON produtos
                    WHEN NEW.nome IS NULL OR length(NEW.nome) NOT BETWEEN 2 AND 200 OR NEW.preco IS NULL OR NEW.preco < 0 OR NEW.estoque IS NULL OR NEW.estoque < 0 OR NEW.categoria NOT IN ('informatica','moveis','vestuario','geral','eletronicos','livros')
                    BEGIN SELECT RAISE(ABORT, 'produto inválido'); END;
                    CREATE TRIGGER IF NOT EXISTS pedidos_validate_insert
                    BEFORE INSERT ON pedidos
                    WHEN NEW.usuario_id IS NULL OR (SELECT id FROM usuarios WHERE id = NEW.usuario_id) IS NULL OR NEW.status NOT IN ('pendente','aprovado','enviado','entregue','cancelado') OR NEW.total IS NULL OR NEW.total < 0
                    BEGIN SELECT RAISE(ABORT, 'pedido inválido'); END;
                    CREATE TRIGGER IF NOT EXISTS pedidos_validate_update
                    BEFORE UPDATE ON pedidos
                    WHEN NEW.usuario_id IS NULL OR (SELECT id FROM usuarios WHERE id = NEW.usuario_id) IS NULL OR NEW.status NOT IN ('pendente','aprovado','enviado','entregue','cancelado') OR NEW.total IS NULL OR NEW.total < 0
                    BEGIN SELECT RAISE(ABORT, 'pedido inválido'); END;
                    CREATE TRIGGER IF NOT EXISTS itens_validate_insert
                    BEFORE INSERT ON itens_pedido
                    WHEN NEW.pedido_id IS NULL OR (SELECT id FROM pedidos WHERE id = NEW.pedido_id) IS NULL OR NEW.produto_id IS NULL OR (SELECT id FROM produtos WHERE id = NEW.produto_id) IS NULL OR NEW.quantidade IS NULL OR NEW.quantidade <= 0 OR NEW.preco_unitario IS NULL OR NEW.preco_unitario < 0
                    BEGIN SELECT RAISE(ABORT, 'item de pedido inválido'); END;
                    CREATE TRIGGER IF NOT EXISTS itens_validate_update
                    BEFORE UPDATE ON itens_pedido
                    WHEN NEW.pedido_id IS NULL OR (SELECT id FROM pedidos WHERE id = NEW.pedido_id) IS NULL OR NEW.produto_id IS NULL OR (SELECT id FROM produtos WHERE id = NEW.produto_id) IS NULL OR NEW.quantidade IS NULL OR NEW.quantidade <= 0 OR NEW.preco_unitario IS NULL OR NEW.preco_unitario < 0
                    BEGIN SELECT RAISE(ABORT, 'item de pedido inválido'); END;
                    CREATE TRIGGER IF NOT EXISTS usuarios_prevent_delete_with_orders
                    BEFORE DELETE ON usuarios
                    WHEN EXISTS (SELECT 1 FROM pedidos WHERE usuario_id = OLD.id)
                    BEGIN SELECT RAISE(ABORT, 'usuário possui pedidos'); END;
                    CREATE TRIGGER IF NOT EXISTS produtos_prevent_delete_with_items
                    BEFORE DELETE ON produtos
                    WHEN EXISTS (SELECT 1 FROM itens_pedido WHERE produto_id = OLD.id)
                    BEGIN SELECT RAISE(ABORT, 'produto possui itens de pedidos'); END;
                    """
                )
                product_count = connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
                if product_count == 0:
                    connection.executemany(
                        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                        PRODUCT_SEED,
                    )

                # Existing installations used plaintext credentials. Migrate them in place
                # on first application use without exposing the original value.
                for row in connection.execute("SELECT id, senha FROM usuarios").fetchall():
                    if not hasher.is_hash(row["senha"]):
                        connection.execute(
                            "UPDATE usuarios SET senha = ? WHERE id = ?",
                            (hasher.hash(row["senha"]), row["id"]),
                        )
                if bootstrap_email and bootstrap_password:
                    existing = connection.execute(
                        "SELECT id FROM usuarios WHERE email = ? COLLATE NOCASE",
                        (bootstrap_email.lower(),),
                    ).fetchone()
                    if existing is None:
                        connection.execute(
                            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, 'admin')",
                            ("Administrador", bootstrap_email.lower(), hasher.hash(bootstrap_password)),
                        )
                connection.commit()
            self._initialized = True

    def reset(self) -> None:
        with self.transaction() as connection:
            connection.execute("DELETE FROM itens_pedido")
            connection.execute("DELETE FROM pedidos")
            connection.execute("DELETE FROM produtos")
            connection.execute("DELETE FROM usuarios")

    def health(self) -> dict:
        with self.connection() as connection:
            connection.execute("SELECT 1").fetchone()
            counts = {
                "produtos": connection.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
                "usuarios": connection.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
                "pedidos": connection.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
            }
        return {
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": "1.0.0",
            "ambiente": "configured",
        }
