"""Configuração externa (variáveis de ambiente / arquivo .env).

Nenhum segredo fica no código: valores obrigatórios ausentes interrompem a
inicialização com uma mensagem clara. Veja `.env.example`.
"""
import os
from dataclasses import dataclass
from typing import Mapping, Optional

from dotenv import load_dotenv

_TRUE_VALUES = ('1', 'true', 'yes', 'on')


class ConfigError(RuntimeError):
    """Configuração obrigatória ausente ou inválida."""


def _required(env: Mapping[str, str], name: str) -> str:
    value = env.get(name)
    if not value:
        raise ConfigError(
            f'Missing required config: {name} (defina no ambiente ou em .env; veja .env.example)'
        )
    return value


def _as_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None or value == '':
        return default
    return value.strip().lower() in _TRUE_VALUES


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_uri: str
    debug: bool
    host: str
    port: int
    cors_origins: str
    token_max_age_seconds: int
    log_level: str
    email_host: str
    email_port: int
    email_user: Optional[str]
    email_password: Optional[str]

    def flask_config(self) -> dict:
        return {
            'SECRET_KEY': self.secret_key,
            'SQLALCHEMY_DATABASE_URI': self.database_uri,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'TOKEN_MAX_AGE_SECONDS': self.token_max_age_seconds,
        }


def load_settings(env: Optional[Mapping[str, str]] = None) -> Settings:
    """Lê as configurações. Sem `env`, carrega `.env` (se existir) e usa os.environ."""
    if env is None:
        load_dotenv()
        env = os.environ

    try:
        port = int(env.get('PORT', '5000'))
        email_port = int(env.get('EMAIL_PORT', '587'))
        token_max_age = int(env.get('TOKEN_MAX_AGE_SECONDS', '86400'))
    except ValueError as exc:
        raise ConfigError(f'Valor numérico inválido na configuração: {exc}') from exc

    return Settings(
        secret_key=_required(env, 'SECRET_KEY'),
        database_uri=env.get('DATABASE_URL', 'sqlite:///tasks.db'),
        debug=_as_bool(env.get('APP_DEBUG'), default=False),
        host=env.get('HOST', '127.0.0.1'),
        port=port,
        cors_origins=env.get('CORS_ORIGINS', '*'),
        token_max_age_seconds=token_max_age,
        log_level=env.get('LOG_LEVEL', 'INFO').upper(),
        email_host=env.get('EMAIL_HOST', 'smtp.gmail.com'),
        email_port=email_port,
        email_user=env.get('EMAIL_USER') or None,
        email_password=env.get('EMAIL_PASSWORD') or None,
    )
