"""Relógio central com UTC sem timezone para compatibilidade com o schema legado."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Retorna UTC naive, preservando serialização e dados SQLite existentes."""

    return datetime.now(UTC).replace(tzinfo=None)
