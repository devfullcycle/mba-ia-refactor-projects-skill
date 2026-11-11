import re
from datetime import datetime

from src.utils.dates import DATE_FORMAT
from src.utils.errors import ValidationError

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def require_json_object(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError("Dados inválidos")
    return data


def required_string(value, message):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(message)
    return value.strip()


def optional_string(value, field_label):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field_label} deve ser texto")
    return value


def string_length(value, min_length, max_length, too_short, too_long):
    if len(value) < min_length:
        raise ValidationError(too_short)
    if len(value) > max_length:
        raise ValidationError(too_long)
    return value


def int_in_range(value, min_value, max_value, out_of_range, invalid):
    # bool é subclasse de int em Python: True não pode virar prioridade 1.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(invalid)
    if value < min_value or value > max_value:
        raise ValidationError(out_of_range)
    return value


def optional_id(value, field_label):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValidationError(f"{field_label} inválido")
    return value


def query_int(value, field_label):
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_label} inválido")


def boolean(value, field_label):
    if not isinstance(value, bool):
        raise ValidationError(f"{field_label} deve ser true ou false")
    return value


def choice(value, allowed, message):
    if value not in allowed:
        raise ValidationError(message)
    return value


def email(value):
    value = required_string(value, "Email é obrigatório").lower()
    if not EMAIL_REGEX.match(value):
        raise ValidationError("Email inválido")
    return value


def color(value):
    if not isinstance(value, str) or not COLOR_REGEX.match(value):
        raise ValidationError("Cor inválida. Use o formato #RRGGBB")
    return value


def date(value):
    if not isinstance(value, str):
        raise ValidationError("Formato de data inválido. Use YYYY-MM-DD")
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError("Formato de data inválido. Use YYYY-MM-DD")


def tags(value):
    if value is None:
        return None
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise ValidationError("Tags devem ser texto")
        cleaned = [tag.strip() for tag in value if tag.strip()]
        return ",".join(cleaned) or None
    if isinstance(value, str):
        return value or None
    raise ValidationError("Tags devem ser uma lista ou texto separado por vírgulas")
