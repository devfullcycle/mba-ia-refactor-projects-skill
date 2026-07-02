import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me-in-production")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
STATUSES_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

FAIXA_DESCONTO_ALTO = 10000
TAXA_DESCONTO_ALTO = 0.10

FAIXA_DESCONTO_MEDIO = 5000
TAXA_DESCONTO_MEDIO = 0.05

FAIXA_DESCONTO_BAIXO = 1000
TAXA_DESCONTO_BAIXO = 0.02
