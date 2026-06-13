from dataclasses import dataclass
from pathlib import Path
import os
import secrets

from dotenv import load_dotenv


def _truthy(value: str | None) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    database_path: str
    admin_api_token: str


def load_settings(overrides: dict | None = None) -> Settings:
    load_dotenv(Path(__file__).resolve().parent / ".env")
    data = overrides or {}

    secret_key = (
        data.get("SECRET_KEY")
        or os.getenv("SECRET_KEY")
        or secrets.token_hex(32)
    )
    debug = bool(data.get("DEBUG")) if "DEBUG" in data else _truthy(os.getenv("FLASK_DEBUG"))
    database_path = data.get("DATABASE") or os.getenv("LOJA_DB_PATH") or "loja.db"
    admin_api_token = data.get("ADMIN_API_TOKEN") or os.getenv("ADMIN_API_TOKEN") or ""

    return Settings(
        secret_key=secret_key,
        debug=debug,
        database_path=database_path,
        admin_api_token=admin_api_token,
    )
