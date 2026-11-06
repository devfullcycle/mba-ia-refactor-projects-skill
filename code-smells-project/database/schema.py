"""DDL e seed do banco — separados do ciclo de vida da conexão.

Mantém o bootstrap atual (schema criado no primeiro acesso, seed com
produtos e usuários) preservando o comportamento observável. A adoção de
migrations versionadas (QUAL-06) fica registrada como trabalho futuro:
aqui o schema permanece inline para não alterar o contrato de boot.

SEC-03: o seed grava apenas hashes com salt (werkzeug/scrypt). Bancos criados
por versões antigas têm senhas em texto puro re-hasheadas no boot por
``migrate_legacy_passwords`` — antes de qualquer autenticação.
"""

from werkzeug.security import generate_password_hash

_PREFIXOS_HASH = ("pbkdf2:", "scrypt:", "argon2")

PRODUTOS_SEED = [
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

# Hashes pré-computados (werkzeug scrypt) das credenciais de desenvolvimento
# documentadas no README. Nenhuma senha em texto puro é persistida no seed.
USUARIOS_SEED = [
    (
        "Admin",
        "admin@loja.com",
        "scrypt:32768:8:1$Q3EVMnGz18bqJswv$090599a64657c329442f05be861f119ca9cff97011ce70a54fd7f9f5cd84a539cbfa0a65f664f8576822c9b431fe436af57bdeddaddb55f8798f2089e6034e9e",
        "admin",
    ),
    (
        "João Silva",
        "joao@email.com",
        "scrypt:32768:8:1$5q2GTV5Ndyjs1BpJ$c82eaedaf5cf6018c1133fd81f42a8179a3da3c688689081f33c2f275a61a817ac909f8717af7460057c980526a6da07697b04f174037aa6cf749a7751664861",
        "cliente",
    ),
    (
        "Maria Santos",
        "maria@email.com",
        "scrypt:32768:8:1$52o1Js9G8goBatQh$148e26bfb0f72cd247ce9ee731f384baae3c16ea0d5cc92befd4435841cf45386e2606dbd25832ede3cc12934ddfbbfc49fcf2314d98a6ee67490530fd047a81",
        "cliente",
    ),
]

_DDL = (
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


def _senha_legada(stored):
    """True apenas para valores sem prefixo de hash (texto puro legado)."""
    return bool(stored) and not str(stored).startswith(_PREFIXOS_HASH)


def migrate_legacy_passwords(conn):
    """Re-hasheia senhas legadas em texto puro; idempotente e executada no boot.

    A rotina roda antes de qualquer autenticação. O login nunca compara texto
    puro: se um registro legado escapar da migração, a autenticação falha
    fechada em vez de aceitar a senha em claro.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id, senha FROM usuarios")
    updates = [
        (generate_password_hash(str(stored)), usuario_id)
        for usuario_id, stored in cursor.fetchall()
        if _senha_legada(stored)
    ]
    if updates:
        cursor.executemany("UPDATE usuarios SET senha = ? WHERE id = ?", updates)
        conn.commit()
    return len(updates)


def ensure_schema(conn):
    """Cria as tabelas e popula o seed apenas no primeiro boot do banco.

    O seed roda uma única vez por arquivo de banco (controlado por uma
    tabela de metadados), para que `/admin/reset-db` esvazie de verdade e
    a base não seja repovoada a cada nova conexão. A migração de senhas
    legadas roda em todo boot, inclusive em bancos já semeados.
    """
    cursor = conn.cursor()
    for ddl in _DDL:
        cursor.execute(ddl)
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS _meta (chave TEXT PRIMARY KEY, valor TEXT)"
    )
    conn.commit()

    cursor.execute("SELECT valor FROM _meta WHERE chave = 'seed_aplicado'")
    if cursor.fetchone() is None:
        cursor.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_SEED,
        )
        cursor.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            USUARIOS_SEED,
        )
        cursor.execute("INSERT INTO _meta (chave, valor) VALUES ('seed_aplicado', '1')")
        conn.commit()

    migrate_legacy_passwords(conn)
