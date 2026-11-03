"""Dados de exemplo para desenvolvimento (desative com SEED_DB=false)."""
from flask import current_app

from src.models import produto_model, usuario_model

PRODUTOS_INICIAIS = (
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


def seed_if_empty():
    if produto_model.contar() > 0:
        return

    for nome, descricao, preco, estoque, categoria in PRODUTOS_INICIAIS:
        produto_model.criar(nome, descricao, preco, estoque, categoria)

    usuarios = (
        ("Admin", "admin@loja.com", current_app.config["SEED_ADMIN_PASSWORD"], "admin"),
        ("João Silva", "joao@email.com", "123456", "cliente"),
        ("Maria Santos", "maria@email.com", "senha123", "cliente"),
    )
    for nome, email, senha, tipo in usuarios:
        usuario_model.criar(nome, email, senha, tipo)
