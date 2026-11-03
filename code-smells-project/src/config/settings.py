"""Configuração centralizada: única camada que lê variáveis de ambiente."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _env_bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _secret_key():
    key = os.environ.get("SECRET_KEY")
    if key:
        return key
    logger.warning("SECRET_KEY não definida; usando chave efêmera (apenas para desenvolvimento).")
    return secrets.token_hex(32)


class Settings:
    APP_NAME = "API da Loja"
    APP_VERSION = "1.0.0"
    APP_ENV = os.environ.get("APP_ENV", "development")

    SECRET_KEY = _secret_key()
    DEBUG = _env_bool("FLASK_DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    SEED_DATABASE = _env_bool("SEED_DATABASE", True)

    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Endpoints /admin/* ficam desabilitados (403) enquanto ADMIN_TOKEN não for definido.
    ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
