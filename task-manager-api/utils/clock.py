"""Helpers de data/hora (substituem o deprecated datetime.utcnow)."""
from datetime import datetime, timezone

DATE_FORMATS = ("%Y-%m-%d",)


def utcnow():
    """UTC *naive* — compatível com as colunas DateTime (sem timezone) já existentes no banco."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_str(value):
    return str(value) if value else None


def parse_date(value):
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except (TypeError, ValueError):
            continue
    return None
