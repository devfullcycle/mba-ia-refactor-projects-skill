"""Utilitários de data/hora.

`datetime.utcnow()` está deprecada desde o Python 3.12 e o legado a usava em 18 pontos.
A substituição preserva a semântica de armazenamento do projeto: as colunas `DateTime` do
SQLite guardam datetimes *naive*, então mantemos UTC ingênuo em vez de introduzir datetimes
*aware* — misturar os dois levantaria `TypeError` nas comparações.

Migrar o projeto inteiro para datetimes com fuso é uma mudança separada, que exigiria
`DateTime(timezone=True)` nas colunas e alteraria o formato das respostas.
"""
from datetime import datetime, timezone

from src.domain.constants import DATE_INPUT_FORMATS


def now_utc():
    """Instante atual em UTC, sem tzinfo (substitui `datetime.utcnow()`)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(value):
    """Converte string de data para datetime, ou devolve None se o formato for inválido."""
    if not value:
        return None
    for formato in DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(value, formato)
        except (TypeError, ValueError):
            continue
    return None
