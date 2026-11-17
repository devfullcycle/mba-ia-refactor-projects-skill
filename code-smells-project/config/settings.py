import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
    DB_PATH = os.getenv("DB_PATH", "loja.db")
    PORT = int(os.getenv("PORT", "5000"))
    HOST = os.getenv("HOST", "0.0.0.0")

    # Domain Constants
    VALID_CATEGORIES = [
        "informatica",
        "moveis",
        "vestuario",
        "geral",
        "eletronicos",
        "livros"
    ]
    
    VALID_ORDER_STATUSES = [
        "pendente",
        "aprovado",
        "enviado",
        "entregue",
        "cancelado"
    ]

    # Business Rules: Discount thresholds
    DISCOUNT_TIERS = [
        (10000.0, 0.10),
        (5000.0, 0.05),
        (1000.0, 0.02)
    ]
