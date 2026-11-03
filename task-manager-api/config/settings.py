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
    logger.warning("SECRET_KEY não definida; usando chave efêmera (tokens expiram a cada restart).")
    return secrets.token_hex(32)


class Settings:
    APP_NAME = "Task Manager API"
    APP_VERSION = "1.0"

    SECRET_KEY = _secret_key()
    DEBUG = _env_bool("FLASK_DEBUG", False)
    HOST = os.environ.get("HOST", "127.0.0.1")
    PORT = int(os.environ.get("PORT", "5000"))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AUTH_TOKEN_MAX_AGE_SECONDS = int(os.environ.get("AUTH_TOKEN_MAX_AGE_SECONDS", "3600"))

    # Notificações por e-mail desabilitadas por padrão (apenas log) até o SMTP ser configurado.
    EMAIL_ENABLED = _env_bool("EMAIL_ENABLED", False)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
