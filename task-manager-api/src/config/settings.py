"""Application settings, read exclusively from environment variables."""
import logging
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def _bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _tuple(name, default):
    raw = os.environ.get(name, default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    debug: bool
    host: str
    port: int
    cors_origins: tuple
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
        logger.warning("SECRET_KEY not set; using a random ephemeral key (tokens expire on restart)")
    return Settings(
        secret_key=secret_key,
        database_url=os.environ.get("DATABASE_URL", "sqlite:///tasks.db"),
        debug=_bool("FLASK_DEBUG", False),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        cors_origins=_tuple("CORS_ORIGINS", "*"),
        token_max_age=int(os.environ.get("TOKEN_MAX_AGE", "86400")),
        smtp_host=os.environ.get("SMTP_HOST", ""),
        smtp_port=int(os.environ.get("SMTP_PORT", "587")),
        smtp_user=os.environ.get("SMTP_USER", ""),
        smtp_password=os.environ.get("SMTP_PASSWORD", ""),
    )
