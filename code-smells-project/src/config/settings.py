"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


CATEGORIAS_VALIDAS = (
    "informatica",
    "moveis",
    "vestuario",
    "geral",
    "eletronicos",
    "livros",
)

STATUS_PEDIDO_VALIDOS = (
    "pendente",
    "aprovado",
    "enviado",
    "entregue",
    "cancelado",
)

# Discount tiers for sales report (faturamento threshold → rate)
DESCONTO_FAIXAS: tuple[tuple[float, float], ...] = (
    (10_000.0, 0.10),
    (5_000.0, 0.05),
    (1_000.0, 0.02),
)


@dataclass(frozen=True)
class Settings:
    secret_key: str
    debug: bool
    host: str
    port: int
    db_path: str
    ambiente: str
    admin_token: str | None


def load_settings() -> Settings:
    return Settings(
        secret_key=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5003")),
        db_path=os.environ.get("DB_PATH", "loja.db"),
        ambiente=os.environ.get("AMBIENTE", "desenvolvimento"),
        admin_token=os.environ.get("ADMIN_TOKEN"),
    )
