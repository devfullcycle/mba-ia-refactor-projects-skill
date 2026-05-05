import os


class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    ENABLE_ADMIN_RESET = os.environ.get("ENABLE_ADMIN_RESET", "false").lower() in ("1", "true", "yes")
