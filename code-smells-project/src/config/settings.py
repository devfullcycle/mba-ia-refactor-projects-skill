"""Configuração da aplicação lida de variáveis de ambiente (sem segredos literais)."""
import logging
import os
import secrets
from dataclasses import dataclass

API_VERSION = "1.0.0"

logger = logging.getLogger(__name__)


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_path: str
    environment: str
    cors_origins: str
    admin_token: str


def load_settings() -> Settings:
    secret_key = os.environ.get("SECRET_KEY", "")
    if not secret_key:
        secret_key = secrets.token_hex(32)
        logger.warning("SECRET_KEY não definida; usando chave aleatória efêmera")

    return Settings(
        secret_key=secret_key,
        debug=_bool("FLASK_DEBUG", False),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        database_path=os.environ.get("DATABASE_PATH", "loja.db"),
        environment=os.environ.get("APP_ENV", "desenvolvimento"),
        cors_origins=os.environ.get("CORS_ORIGINS", "*"),
        admin_token=os.environ.get("ADMIN_TOKEN", ""),
    )
