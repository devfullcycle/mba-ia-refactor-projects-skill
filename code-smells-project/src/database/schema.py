"""Schema, seed e migrações do banco."""
import logging

from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

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

SEED_PRODUTOS = (
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
)

# Usuários de demonstração (ambiente de desenvolvimento). Senhas são gravadas com hash.
SEED_USUARIOS = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)

_HASH_PREFIXES = ("scrypt:", "pbkdf2:")


def create_schema(conn):
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()


def seed(conn):
    if conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    conn.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        SEED_PRODUTOS,
    )
    conn.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in SEED_USUARIOS],
    )
    conn.commit()
    logger.info("Banco populado com dados de exemplo")


def migrate_plaintext_passwords(conn):
    """Converte senhas legadas em texto puro para hash (bancos criados pela versão antiga)."""
    rows = conn.execute("SELECT id, senha FROM usuarios").fetchall()
    legacy = [(row["id"], row["senha"]) for row in rows if row["senha"] and not row["senha"].startswith(_HASH_PREFIXES)]
    if not legacy:
        return
    conn.executemany(
        "UPDATE usuarios SET senha = ? WHERE id = ?",
        [(generate_password_hash(senha), user_id) for user_id, senha in legacy],
    )
    conn.commit()
    logger.warning("%d senha(s) legada(s) em texto puro migrada(s) para hash", len(legacy))


def init_db(conn, with_seed=True):
    create_schema(conn)
    if with_seed:
        seed(conn)
    migrate_plaintext_passwords(conn)
