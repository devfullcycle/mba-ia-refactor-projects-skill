"""Funções utilitárias puras, compartilhadas entre camadas."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    """Data/hora UTC *naive* (mesmo formato antes gravado por `datetime.utcnow()`).

    Substitui `datetime.utcnow()` (deprecated no Python 3.12) sem mudar o formato
    armazenado nem as comparações com colunas DateTime naive.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def calculate_percentage(part, total):
    """Percentual com 2 casas; 0 quando `total` é 0."""
    if total == 0:
        return 0
    return round((part / total) * 100, 2)
