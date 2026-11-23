"""Validações reutilizadas pelos validators de cada recurso."""
import re

from utils.constants import (
    EMAIL_PATTERN, MAX_EMAIL_LENGTH, MAX_NAME_LENGTH, MAX_PAGE_SIZE, MIN_PASSWORD_LENGTH,
)
from utils.errors import ValidationError


def name(value, max_length=MAX_NAME_LENGTH):
    """Texto obrigatório, sem espaços nas pontas e dentro do tamanho da coluna."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError('Nome inválido')
    value = value.strip()
    if len(value) > max_length:
        raise ValidationError(f'Nome deve ter no máximo {max_length} caracteres')
    return value


def optional_text(value, max_length, message):
    """Texto opcional (None ou str) com tamanho máximo."""
    if value is None:
        return None
    if not isinstance(value, str) or len(value) > max_length:
        raise ValidationError(message)
    return value


def email(value):
    """E-mail válido, normalizado em minúsculas (evita contas duplicadas por caixa)."""
    if not isinstance(value, str) or len(value) > MAX_EMAIL_LENGTH or not re.match(EMAIL_PATTERN, value):
        raise ValidationError('Email inválido')
    return value.strip().lower()


def password(value, message=f'Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres'):
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(message)
    return value


def boolean(value, message):
    if not isinstance(value, bool):
        raise ValidationError(message)
    return value


def pagination(args):
    """`?limit=&offset=` opcionais. Sem `limit`, devolve (None, 0): listagem completa, como antes."""
    raw_limit, raw_offset = args.get('limit', ''), args.get('offset', '')
    try:
        limit = int(raw_limit) if raw_limit else None
        offset = int(raw_offset) if raw_offset else 0
    except ValueError:
        raise ValidationError('Parâmetros de paginação inválidos')
    if (limit is not None and not 1 <= limit <= MAX_PAGE_SIZE) or offset < 0:
        raise ValidationError(f'limit deve estar entre 1 e {MAX_PAGE_SIZE} e offset >= 0')
    return limit, offset
