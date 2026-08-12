"""Configurações centralizadas da aplicação.

Segredos e parâmetros sensíveis são lidos de variáveis de ambiente,
nunca hardcoded no código.
"""

import os

# Segredos e parâmetros sensíveis (via env)
SECRET_KEY = os.environ.get("SECRET_KEY", "troque-esta-chave-em-producao")
DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
DB_PATH = os.environ.get("DB_PATH", "loja.db")

# Categorias de produto permitidas (regra de domínio)
CATEGORIAS_VALIDAS = [
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
]

# Faixas de desconto aplicadas no relatório de vendas (regra de negócio)
DESCONTO_FAIXAS = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]

# Status válidos de pedido
STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]