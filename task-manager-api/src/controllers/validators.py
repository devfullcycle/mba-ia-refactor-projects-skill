"""Input validation shared by create and update use cases. Error messages are part of the API contract."""
import re
from datetime import datetime

from src.controllers.errors import ValidationError
from src.models.task_model import (
    PRIORITY_MAX, PRIORITY_MIN, TAG_SEPARATOR, TASK_STATUSES, TITLE_MAX_LENGTH, TITLE_MIN_LENGTH,
)
from src.models.user_model import MIN_PASSWORD_LENGTH, USER_ROLES

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
DUE_DATE_FORMAT = "%Y-%m-%d"
INVALID_DATA = "Dados inválidos"


def require_body(data, allow_empty=False):
    if not isinstance(data, dict) or (not data and not allow_empty):
        raise ValidationError(INVALID_DATA)
    return data


def validate_title(title, required=True):
    if title is None or (required and not title):
        raise ValidationError("Título é obrigatório")
    if not isinstance(title, str):
        raise ValidationError("Título inválido")
    if len(title) < TITLE_MIN_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def validate_status(status):
    if not isinstance(status, str) or status not in TASK_STATUSES:
        raise ValidationError("Status inválido")
    return status


def validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int):
        raise ValidationError("Prioridade inválida")
    if not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")
    return priority


def parse_due_date(value, error_message):
    try:
        return datetime.strptime(value, DUE_DATE_FORMAT)
    except (TypeError, ValueError):
        raise ValidationError(error_message) from None


def normalize_tags(tags):
    if isinstance(tags, list):
        return TAG_SEPARATOR.join(str(tag) for tag in tags)
    return None if tags is None else str(tags)


def coerce_id(value):
    """Int id from JSON (int or digit string); None when it cannot reference any row."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value)
    return None


def parse_int_query(value, error_message):
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        raise ValidationError(error_message) from None


def validate_name(name):
    if not name or not isinstance(name, str):
        raise ValidationError("Nome é obrigatório")
    return name


def validate_email(email):
    if not isinstance(email, str) or not EMAIL_REGEX.match(email):
        raise ValidationError("Email inválido")
    return email


def validate_password(password, error_message):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(error_message)
    return password


def validate_role(role):
    if not isinstance(role, str) or role not in USER_ROLES:
        raise ValidationError("Role inválido")
    return role


def validate_active(active):
    if not isinstance(active, bool):
        raise ValidationError("Valor de active inválido")
    return active
