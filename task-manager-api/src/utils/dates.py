from datetime import datetime, timezone

DATE_FORMAT = "%Y-%m-%d"


def utc_now():
    """UTC atual como datetime naive (substitui o deprecated datetime.utcnow()).

    Mantém o formato naive porque os registros existentes no SQLite foram gravados assim.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def format_datetime(value):
    return str(value) if value else None
