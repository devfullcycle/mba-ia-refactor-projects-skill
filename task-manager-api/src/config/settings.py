import logging
import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

# Raiz do projeto (task-manager-api/): caminhos relativos não dependem do diretório de execução.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")

logger = logging.getLogger(__name__)

PRODUCTION_ENV = "production"


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _env_list(name):
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


def _default_database_url():
    # O legado usava 'sqlite:///tasks.db', que o Flask-SQLAlchemy 3 resolve dentro de instance/.
    return f"sqlite:///{(PROJECT_ROOT / 'instance' / 'tasks.db').as_posix()}"


class Config:
    APP_NAME = "Task Manager API"
    APP_VERSION = "1.0"
    APP_ENV = os.getenv("APP_ENV", PRODUCTION_ENV)

    SECRET_KEY = os.getenv("SECRET_KEY")
    TOKEN_TTL_SECONDS = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))

    DEBUG = _env_bool("DEBUG", False)
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Vazio = CORS desabilitado (apenas mesma origem).
    CORS_ORIGINS = _env_list("CORS_ORIGINS")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _default_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paginação opcional (?page=&per_page=) nas listagens.
    DEFAULT_PER_PAGE = int(os.getenv("DEFAULT_PER_PAGE", "20"))
    MAX_PER_PAGE = int(os.getenv("MAX_PER_PAGE", "100"))

    # Notificações por e-mail ficam desabilitadas até SMTP_ENABLED=true.
    SMTP_ENABLED = _env_bool("SMTP_ENABLED", False)
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

    # Seed é opt-in e nunca roda em produção; senhas não informadas são geradas aleatoriamente.
    SEED_DB = _env_bool("SEED_DB", False)
    SEED_ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD") or None
    SEED_USER_PASSWORD = os.getenv("SEED_USER_PASSWORD") or None
    SEED_MANAGER_PASSWORD = os.getenv("SEED_MANAGER_PASSWORD") or None

    @classmethod
    def is_production(cls):
        return cls.APP_ENV == PRODUCTION_ENV

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            cls.SECRET_KEY = secrets.token_hex(32)
            logger.warning(
                "SECRET_KEY não definida; usando chave aleatória temporária "
                "(tokens de login deixam de valer ao reiniciar o processo)."
            )
