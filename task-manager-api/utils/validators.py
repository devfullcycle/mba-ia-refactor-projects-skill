"""Validação de entrada reutilizável. Lança AppError(400) com as mensagens originais da API."""
import re
from datetime import datetime

from config.constants import (
    COLOR_LENGTH,
    DATE_FORMAT,
    EMAIL_REGEX,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_TITLE_LENGTH,
    PRIORITY_MAX,
    PRIORITY_MIN,
    VALID_ROLES,
    VALID_STATUSES,
)
from utils.errors import AppError


def require_json_object(data, allow_empty=False):
    """Corpo precisa ser um objeto JSON (e, por padrão, não vazio)."""
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise AppError('Dados inválidos', 400)
    return data


def validate_title(value, required_message=None):
    if required_message and not value:
        raise AppError(required_message, 400)
    if not isinstance(value, str):
        raise AppError('Título inválido', 400)
    if len(value) < MIN_TITLE_LENGTH:
        raise AppError('Título muito curto', 400)
    if len(value) > MAX_TITLE_LENGTH:
        raise AppError('Título muito longo', 400)
    return value


def validate_status(value):
    if value not in VALID_STATUSES:
        raise AppError('Status inválido', 400)
    return value


def validate_priority(value):
    message = f'Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}'
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not float(value).is_integer():
        raise AppError(message, 400)
    value = int(value)
    if value < PRIORITY_MIN or value > PRIORITY_MAX:
        raise AppError(message, 400)
    return value


def parse_due_date(value, message):
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (ValueError, TypeError):
        raise AppError(message, 400)


def normalize_tags(value):
    """Lista de strings vira 'a,b'; string/None passam como estão."""
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise AppError('Tags inválidas', 400)
        return ','.join(value)
    if value is None or isinstance(value, str):
        return value
    raise AppError('Tags inválidas', 400)


def parse_int_param(value, message):
    try:
        return int(value)
    except (ValueError, TypeError):
        raise AppError(message, 400)


def validate_email(value):
    if not isinstance(value, str) or not re.match(EMAIL_REGEX, value):
        raise AppError('Email inválido', 400)
    return value


def validate_password(value, too_short_message):
    if not isinstance(value, str):
        raise AppError(too_short_message, 400)
    if len(value) < MIN_PASSWORD_LENGTH:
        raise AppError(too_short_message, 400)
    return value


def validate_role(value):
    if value not in VALID_ROLES:
        raise AppError('Role inválido', 400)
    return value


def validate_color(value):
    if not isinstance(value, str) or len(value) != COLOR_LENGTH or not value.startswith('#'):
        raise AppError('Cor inválida', 400)
    return value
