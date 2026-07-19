"""Utilitários de data/hora.

Usa a API moderna `datetime.now(timezone.utc)` (em vez de `datetime.utcnow()`,
deprecated no Python 3.12+) mas retorna um datetime *naive* em UTC para manter
compatibilidade com as colunas SQLAlchemy DateTime (sem timezone) já persistidas.
"""
from datetime import datetime, timezone


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_iso(value):
    return str(value) if value else None
