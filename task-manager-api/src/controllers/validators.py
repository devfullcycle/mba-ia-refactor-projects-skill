"""Input validation shared by create/update use cases. Raises ValidationError (HTTP 400)."""
import re
from datetime import datetime

from src.controllers.errors import ValidationError
from src.models.constants import (
    DATE_FORMAT,
    DEFAULT_COLOR,
    DEFAULT_PRIORITY,
    MAX_PRIORITY,
    MAX_TITLE_LENGTH,
    MIN_PASSWORD_LENGTH,
    MIN_PRIORITY,
    MIN_TITLE_LENGTH,
    ROLE_USER,
    STATUS_PENDING,
    VALID_ROLES,
    VALID_STATUSES,
)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")
COLOR_PATTERN = re.compile(r"^#[0-9A-Fa-f]{6}$")


# ---------- generic helpers ----------

def require_object(data):
    """A missing, empty or non-object JSON body is rejected (same message as before)."""
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    return data


def is_valid_email(email):
    return isinstance(email, str) and EMAIL_PATTERN.match(email) is not None


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _optional_id(value, label):
    if value is None:
        return None
    if not _is_int(value):
        raise ValidationError(f"{label} inválido")
    return value


# ---------- tasks ----------

def _title(value, required_message):
    if not value:
        raise ValidationError(required_message)
    if not isinstance(value, str):
        raise ValidationError("Título deve ser texto")
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError("Título muito curto")
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError("Título muito longo")
    return value


def _status(value):
    if value not in VALID_STATUSES:
        raise ValidationError("Status inválido")
    return value


def _priority(value):
    if not _is_int(value):
        raise ValidationError("Prioridade inválida")
    if value < MIN_PRIORITY or value > MAX_PRIORITY:
        raise ValidationError(f"Prioridade deve ser entre {MIN_PRIORITY} e {MAX_PRIORITY}")
    return value


def _due_date(value, error_message):
    if not value:
        return None
    if not isinstance(value, str):
        raise ValidationError(error_message)
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except ValueError:
        raise ValidationError(error_message) from None


def _tags(value):
    if not value:
        return None
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise ValidationError("Tags inválidas")
        return ",".join(value)
    if isinstance(value, str):
        return value
    raise ValidationError("Tags inválidas")


def parse_task_create(data):
    data = require_object(data)
    fields = {
        "title": _title(data.get("title"), "Título é obrigatório"),
        "description": data.get("description", ""),
        "status": _status(data.get("status", STATUS_PENDING)),
        "priority": _priority(data.get("priority", DEFAULT_PRIORITY)),
        "user_id": _optional_id(data.get("user_id"), "user_id") or None,
        "category_id": _optional_id(data.get("category_id"), "category_id") or None,
        "due_date": _due_date(data.get("due_date"), "Formato de data inválido. Use YYYY-MM-DD"),
        "tags": _tags(data.get("tags")),
    }
    return fields


def parse_task_update(data):
    """Only the keys present in the body are returned (partial update)."""
    data = require_object(data)
    fields = {}
    if "title" in data:
        if data["title"] is None or not isinstance(data["title"], str):
            raise ValidationError("Título deve ser texto")
        fields["title"] = _title(data["title"], "Título muito curto")
    if "description" in data:
        fields["description"] = data["description"]
    if "status" in data:
        fields["status"] = _status(data["status"])
    if "priority" in data:
        fields["priority"] = _priority(data["priority"])
    if "user_id" in data:
        fields["user_id"] = _optional_id(data["user_id"], "user_id")
    if "category_id" in data:
        fields["category_id"] = _optional_id(data["category_id"], "category_id")
    if "due_date" in data:
        fields["due_date"] = _due_date(data["due_date"], "Formato de data inválido")
    if "tags" in data:
        fields["tags"] = _tags(data["tags"])
    return fields


def parse_search_filters(args):
    filters = {"text": args.get("q", ""), "status": args.get("status", ""), "priority": None, "user_id": None}
    for key, message in (("priority", "Prioridade inválida"), ("user_id", "user_id inválido")):
        raw = args.get(key, "")
        if raw:
            try:
                filters[key] = int(raw)
            except ValueError:
                raise ValidationError(message) from None
    return filters


# ---------- users ----------

def _required_text(data, field, missing_message, invalid_message):
    value = data.get(field)
    if not value:
        raise ValidationError(missing_message)
    if not isinstance(value, str):
        raise ValidationError(invalid_message)
    return value


def _email(value):
    if not is_valid_email(value):
        raise ValidationError("Email inválido")
    return value


def _role(value):
    if value not in VALID_ROLES:
        raise ValidationError("Role inválido")
    return value


def parse_user_create(data):
    data = require_object(data)
    name = _required_text(data, "name", "Nome é obrigatório", "Nome inválido")
    email = _required_text(data, "email", "Email é obrigatório", "Email inválido")
    password = _required_text(data, "password", "Senha é obrigatória", "Senha inválida")
    _email(email)
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Senha deve ter no mínimo {MIN_PASSWORD_LENGTH} caracteres")
    return {"name": name, "email": email, "password": password, "role": data.get("role", ROLE_USER)}


def validate_role(role):
    return _role(role)


def parse_user_update(data):
    data = require_object(data)
    fields = {}
    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValidationError("Nome inválido")
        fields["name"] = data["name"]
    if "email" in data:
        fields["email"] = _email(data["email"])
    if "password" in data:
        password = data["password"]
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("Senha muito curta")
        fields["password"] = password
    if "role" in data:
        fields["role"] = _role(data["role"])
    if "active" in data:
        if not isinstance(data["active"], bool):
            raise ValidationError("Active deve ser booleano")
        fields["active"] = data["active"]
    return fields


def parse_login(data):
    data = require_object(data)
    email, password = data.get("email"), data.get("password")
    if not email or not password:
        raise ValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(password, str):
        raise ValidationError("Credenciais inválidas")
    return email, password


# ---------- categories ----------

def _color(value):
    if not isinstance(value, str) or not COLOR_PATTERN.match(value):
        raise ValidationError("Cor inválida. Use o formato #RRGGBB")
    return value


def parse_category_create(data):
    data = require_object(data)
    name = _required_text(data, "name", "Nome é obrigatório", "Nome inválido")
    return {
        "name": name,
        "description": data.get("description", ""),
        "color": _color(data.get("color", DEFAULT_COLOR)),
    }


def parse_category_update(data):
    if not isinstance(data, dict):
        raise ValidationError("Dados inválidos")
    fields = {}
    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValidationError("Nome inválido")
        fields["name"] = data["name"]
    if "description" in data:
        fields["description"] = data["description"]
    if "color" in data:
        fields["color"] = _color(data["color"])
    return fields
