import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "admin-dev-token")

VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
VALID_ORDER_STATUSES = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

DISCOUNT_TIERS = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]
