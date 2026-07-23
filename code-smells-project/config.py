"""External, validated application configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os


class ConfigurationError(ValueError):
    """Raised when required operational configuration is missing or invalid."""


def _as_bool(value: str, *, default: bool = False) -> bool:
    if value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: str = "loja.db"
    secret_key: str = ""
    environment: str = "development"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 5000
    token_ttl_seconds: int = 3600
    cors_origins: str | list[str] = "*"
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        secret_key = os.getenv("APP_SECRET", "").strip()
        if len(secret_key) < 32:
            raise ConfigurationError(
                "APP_SECRET deve ser definido externamente e conter pelo menos 32 caracteres"
            )

        try:
            port = int(os.getenv("APP_PORT", "5000"))
            token_ttl = int(os.getenv("TOKEN_TTL_SECONDS", "3600"))
        except ValueError as exc:
            raise ConfigurationError("APP_PORT e TOKEN_TTL_SECONDS devem ser inteiros") from exc
        if not 1 <= port <= 65535:
            raise ConfigurationError("APP_PORT deve estar entre 1 e 65535")
        if token_ttl <= 0:
            raise ConfigurationError("TOKEN_TTL_SECONDS deve ser positivo")

        admin_email = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip() or None
        admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "") or None
        if (admin_email is None) != (admin_password is None):
            raise ConfigurationError(
                "BOOTSTRAP_ADMIN_EMAIL e BOOTSTRAP_ADMIN_PASSWORD devem ser informados juntos"
            )

        origins = os.getenv("CORS_ORIGINS", "*").strip()
        cors_origins: str | list[str] = "*" if origins == "*" else [item.strip() for item in origins.split(",") if item.strip()]
        return cls(
            database_path=os.getenv("DATABASE_PATH", "loja.db"),
            secret_key=secret_key,
            environment=os.getenv("APP_ENV", "development"),
            debug=_as_bool(os.getenv("APP_DEBUG", "")),
            host=os.getenv("APP_HOST", "127.0.0.1"),
            port=port,
            token_ttl_seconds=token_ttl,
            cors_origins=cors_origins,
            bootstrap_admin_email=admin_email,
            bootstrap_admin_password=admin_password,
        )
