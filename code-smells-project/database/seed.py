import logging

logger = logging.getLogger("app.seed")

PRODUTOS_EXEMPLO = (
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


def _usuarios_exemplo(settings, gerar_hash):
    usuarios = []
    if settings.seed_admin_password:
        usuarios.append(("Admin", "admin@loja.com", gerar_hash(settings.seed_admin_password), "admin"))
    else:
        logger.warning("Seed do admin ignorado: SEED_ADMIN_PASSWORD não definida")
    if settings.seed_cliente_password:
        senha = gerar_hash(settings.seed_cliente_password)
        usuarios.append(("João Silva", "joao@email.com", senha, "cliente"))
        usuarios.append(("Maria Santos", "maria@email.com", senha, "cliente"))
    else:
        logger.warning("Seed de clientes ignorado: SEED_CLIENTE_PASSWORD não definida")
    return usuarios


def semear(conexao, settings, gerar_hash):
    """Popula o banco apenas quando não há produtos (primeiro boot)."""
    if conexao.execute("SELECT COUNT(*) FROM produtos").fetchone()[0] > 0:
        return
    with conexao:
        conexao.executemany(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            PRODUTOS_EXEMPLO,
        )
        conexao.executemany(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            _usuarios_exemplo(settings, gerar_hash),
        )
