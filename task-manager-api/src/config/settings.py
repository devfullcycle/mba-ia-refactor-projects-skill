"""Application settings read from environment variables (and an optional `.env`)."""
import logging
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_MAX_AGE_SECONDS = 8 * 60 * 60


def _bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _origins(raw):
    raw = (raw or "*").strip()
    if raw == "*":
        return "*"
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    debug: bool
    host: str
    port: int
    cors_origins: object
    token_max_age: int
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str


def load_settings() -> Settings:
    load_dotenv()
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        secret_key = secrets.token_hex(32)
        logger.warning("SECRET_KEY não definido; usando chave aleatória efêmera (tokens expiram ao reiniciar)")
    return Settings(
        secret_key=secret_key,
        database_url=os.environ.get("DATABASE_URL", "sqlite:///tasks.db"),
        debug=_bool("DEBUG", False),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        cors_origins=_origins(os.environ.get("CORS_ORIGINS")),
        token_max_age=int(os.environ.get("TOKEN_MAX_AGE", str(DEFAULT_TOKEN_MAX_AGE_SECONDS))),
        smtp_host=os.environ.get("SMTP_HOST", ""),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=os.environ.get("SMTP_USER", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
    )
