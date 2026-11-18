from datetime import datetime, timezone


def utc_now():
    """UTC atual como datetime 'naive' (formato que o SQLite armazena e devolve).

    Substitui datetime.utcnow() (deprecated) sem alterar o formato das datas na API.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
