"""Input validation shared by every controller (single source for each rule)."""
import re
from datetime import datetime

from ..models.task_model import PRIORITY_MAX, PRIORITY_MIN, TAG_SEPARATOR, TASK_STATUSES
from ..models.user_model import USER_ROLES
from .errors import ValidationError

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4
DATE_FORMAT = "%Y-%m-%d"
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")

MSG_INVALID_PAYLOAD = "Dados inválidos"
MSG_INVALID_DATE = "Formato de data inválido. Use YYYY-MM-DD"
MSG_INVALID_PRIORITY = "Prioridade inválida"


def require_payload(data):
    if not data or not isinstance(data, dict):
        raise ValidationError(MSG_INVALID_PAYLOAD)
    return data


def require_dict(data):
    """Like require_payload, but an empty object is accepted (partial updates)."""
    if not isinstance(data, dict):
        raise ValidationError(MSG_INVALID_PAYLOAD)
    return data


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def require_text(value, missing_message):
    if not value or not isinstance(value, str):
        raise ValidationError(missing_message)
    return value


def optional_text(value, message):
    if value is not None and not isinstance(value, str):
        raise ValidationError(message)
    return value


def validate_title(value):
    if not value:
        raise ValidationError("Título é obrigatório")
    if not isinstance(value, str):
        raise ValidationError("Título inválido")
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return value


def validate_status(value):
    if value not in TASK_STATUSES:
        raise ValidationError("Status inválido")
    return value


def validate_priority(value):
    if not _is_int(value):
        raise ValidationError(MSG_INVALID_PRIORITY)
    if not PRIORITY_MIN <= value <= PRIORITY_MAX:
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")
    return value


def parse_due_date(value):
    """Empty values clear the due date; anything else must be YYYY-MM-DD."""
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError(MSG_INVALID_DATE)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError as exc:
        raise ValidationError(MSG_INVALID_DATE) from exc


def normalize_tags(value):
    if not value:
        return None
    if isinstance(value, list):
        return TAG_SEPARATOR.join(str(tag) for tag in value)
    if isinstance(value, str):
        return value
    raise ValidationError("Tags inválidas")


def parse_optional_id(value, message):
    """Falsy → None; ints or digit strings → int; anything else is invalid."""
    if not value:
        return None
    if _is_int(value):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    raise ValidationError(message)


def parse_int_query(value, message):
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValidationError(message) from exc


def validate_email(value):
    if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
        raise ValidationError("Email inválido")
    return value


def validate_password(value):
    if not isinstance(value, str) or len(value) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres")
    return value


def validate_role(value):
    if value not in USER_ROLES:
        raise ValidationError("Role inválido")
    return value


def validate_bool(value, message):
    if not isinstance(value, bool):
        raise ValidationError(message)
    return value
