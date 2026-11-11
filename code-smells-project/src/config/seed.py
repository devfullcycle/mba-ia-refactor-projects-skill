"""Dados de exemplo para desenvolvimento.

Só roda com SEED_DB=true e fora de produção. Cada tabela é semeada de forma idempotente:
produtos apenas se a tabela estiver vazia; usuários apenas se o e-mail ainda não existir.
Senhas não informadas via ambiente são geradas aleatoriamente e exibidas uma única vez no log.
"""
import logging
import secrets

from flask import current_app

from src.config.settings import AMBIENTE_PRODUCAO
from src.models import produto_model, usuario_model

logger = logging.getLogger(__name__)

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

# (nome, email, tipo, chave de configuração da senha)
USUARIOS_INICIAIS = (
    ("Admin", "admin@loja.com", usuario_model.TIPO_ADMIN, "SEED_ADMIN_PASSWORD"),
    ("João Silva", "joao@email.com", usuario_model.TIPO_CLIENTE, "SEED_CLIENTE_PASSWORD"),
    ("Maria Santos", "maria@email.com", usuario_model.TIPO_CLIENTE, "SEED_CLIENTE_PASSWORD"),
)


def _seed_produtos():
    if produto_model.contar() > 0:
        return
    for nome, descricao, preco, estoque, categoria in PRODUTOS_INICIAIS:
        produto_model.criar(nome, descricao, preco, estoque, categoria)


def _seed_usuarios():
    for nome, email, tipo, chave_senha in USUARIOS_INICIAIS:
        if usuario_model.email_existe(email):
            continue
        senha = current_app.config.get(chave_senha)
        if not senha:
            senha = secrets.token_urlsafe(12)
            logger.warning("Seed: usuário %s criado com senha gerada: %s", email, senha)
        usuario_model.criar(nome, email, senha, tipo)


def executar_seed():
    if current_app.config["APP_ENV"] == AMBIENTE_PRODUCAO:
        logger.warning("SEED_DB ignorado: seed de dados de exemplo não é executado em produção.")
        return
    _seed_produtos()
    _seed_usuarios()
