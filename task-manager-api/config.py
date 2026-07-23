"""Configuração operacional carregada do ambiente ou de overrides de teste."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping


class ConfigurationError(RuntimeError):
    """Indica configuração ausente ou inválida antes do boot."""


def _as_bool(value: str | bool | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigurationError(f"Valor booleano inválido: {value!r}")


def _as_int(value: str | int | None, *, default: int, name: str) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(f"{name} deve ser um inteiro") from exc
    if parsed <= 0:
        raise ConfigurationError(f"{name} deve ser maior que zero")
    return parsed


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_uri: str
    cors_origins: tuple[str, ...]
    debug: bool
    host: str
    port: int
    auth_token_ttl_seconds: int
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_timeout_seconds: int

    @classmethod
    def load(cls, overrides: Mapping[str, Any] | None = None) -> "Settings":
        values = dict(overrides or {})

        def value(key: str, env_name: str, default: Any = None) -> Any:
            if key in values:
                return values[key]
            return os.getenv(env_name, default)

        secret_key = value("SECRET_KEY", "TASK_MANAGER_SECRET_KEY")
        if not secret_key:
            raise ConfigurationError(
                "TASK_MANAGER_SECRET_KEY é obrigatória; defina um segredo forte antes do boot"
            )

        raw_origins = value("CORS_ORIGINS", "TASK_MANAGER_CORS_ORIGINS", "")
        if isinstance(raw_origins, str):
            cors_origins = tuple(
                origin.strip() for origin in raw_origins.split(",") if origin.strip()
            )
        else:
            cors_origins = tuple(raw_origins or ())

        return cls(
            secret_key=str(secret_key),
            database_uri=str(
                value(
                    "SQLALCHEMY_DATABASE_URI",
                    "TASK_MANAGER_DATABASE_URI",
                    "sqlite:///tasks.db",
                )
            ),
            cors_origins=cors_origins,
            debug=_as_bool(value("DEBUG", "TASK_MANAGER_DEBUG"), default=False),
            host=str(value("HOST", "TASK_MANAGER_HOST", "127.0.0.1")),
            port=_as_int(
                value("PORT", "TASK_MANAGER_PORT"), default=5000, name="TASK_MANAGER_PORT"
            ),
            auth_token_ttl_seconds=_as_int(
                value("AUTH_TOKEN_TTL_SECONDS", "TASK_MANAGER_AUTH_TOKEN_TTL_SECONDS"),
                default=3600,
                name="TASK_MANAGER_AUTH_TOKEN_TTL_SECONDS",
            ),
            smtp_host=value("SMTP_HOST", "TASK_MANAGER_SMTP_HOST"),
            smtp_port=_as_int(
                value("SMTP_PORT", "TASK_MANAGER_SMTP_PORT"),
                default=587,
                name="TASK_MANAGER_SMTP_PORT",
            ),
            smtp_user=value("SMTP_USER", "TASK_MANAGER_SMTP_USER"),
            smtp_password=value("SMTP_PASSWORD", "TASK_MANAGER_SMTP_PASSWORD"),
            smtp_timeout_seconds=_as_int(
                value("SMTP_TIMEOUT_SECONDS", "TASK_MANAGER_SMTP_TIMEOUT_SECONDS"),
                default=10,
                name="TASK_MANAGER_SMTP_TIMEOUT_SECONDS",
            ),
        )

    def flask_config(self) -> dict[str, Any]:
        return {
            "SECRET_KEY": self.secret_key,
            "SQLALCHEMY_DATABASE_URI": self.database_uri,
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "DEBUG": self.debug,
            "AUTH_TOKEN_TTL_SECONDS": self.auth_token_ttl_seconds,
        }
