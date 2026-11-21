"""Configuração externa (variáveis de ambiente). Sem segredos no código."""
import os
from dataclasses import dataclass
from typing import Optional


class ConfigError(RuntimeError):
    """Configuração obrigatória ausente ou inválida."""


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError("Configuração obrigatória ausente: " + name)
    return value


def _as_bool(value: str) -> bool:
    return value.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    database_path: str
    admin_token: Optional[str]
    cors_origins: str
    environment: str
    log_level: str


def load_settings() -> Settings:
    try:
        port = int(os.environ.get("PORT", "5000"))
    except ValueError:
        raise ConfigError("PORT deve ser um inteiro")

    return Settings(
        secret_key=_required("SECRET_KEY"),
        debug=_as_bool(os.environ.get("APP_DEBUG", "false")),
        host=os.environ.get("HOST", "127.0.0.1"),
        port=port,
        database_path=os.environ.get("DATABASE_PATH", "loja.db"),
        admin_token=os.environ.get("ADMIN_TOKEN", "").strip() or None,
        cors_origins=os.environ.get("CORS_ORIGINS", "*"),
        environment=os.environ.get("APP_ENV", "producao"),
        log_level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    )
