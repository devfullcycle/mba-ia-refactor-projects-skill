"""Environment-based configuration. No secret is ever stored as a literal here."""
import logging
import os
import secrets
from dataclasses import dataclass

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_DATABASE_URL = "sqlite:///tasks.db"  # Flask-SQLAlchemy 3 resolves it to instance/tasks.db
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000
DEFAULT_TOKEN_MAX_AGE = 8 * 60 * 60  # seconds
DEFAULT_SMTP_PORT = 587


def _bool(name, default=False):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


def _origins(value):
    origins = [origin.strip() for origin in value.split(",") if origin.strip()]
    return "*" if not origins or origins == ["*"] else origins


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    user: str
    password: str

    @property
    def configured(self):
        return bool(self.host and self.user and self.password)


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_url: str
    cors_origins: object
    token_max_age: int
    smtp: SmtpSettings


def load_settings():
    load_dotenv()
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        secret_key = secrets.token_hex(32)
        logger.warning("SECRET_KEY not set; using a random ephemeral key (tokens expire on restart)")
    return Settings(
        secret_key=secret_key,
        debug=_bool("FLASK_DEBUG", False),
        host=os.environ.get("HOST", DEFAULT_HOST),
        port=int(os.environ.get("PORT", DEFAULT_PORT)),
        database_url=os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL),
        cors_origins=_origins(os.environ.get("CORS_ORIGINS", "*")),
        token_max_age=int(os.environ.get("TOKEN_MAX_AGE", DEFAULT_TOKEN_MAX_AGE)),
        smtp=SmtpSettings(
            host=os.environ.get("SMTP_HOST", ""),
            port=int(os.environ.get("SMTP_PORT", DEFAULT_SMTP_PORT)),
            user=os.environ.get("SMTP_USER", ""),
            password=os.environ.get("SMTP_PASSWORD", ""),
        ),
    )
