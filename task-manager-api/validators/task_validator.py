"""Validação de entrada de Task — regra única para criação, atualização e busca."""
from models.task import (DEFAULT_PRIORITY, PRIORITY_MAX, PRIORITY_MIN, STATUS_PENDING, TITLE_MAX_LENGTH,
                         TITLE_MIN_LENGTH, VALID_STATUSES)
from utils.clock import parse_date
from utils.errors import ValidationError


def _require_dict(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")


def _validate_title(title):
    if not isinstance(title, str) or len(title) < TITLE_MIN_LENGTH:
        raise ValidationError("Título muito curto")
    if len(title) > TITLE_MAX_LENGTH:
        raise ValidationError("Título muito longo")
    return title


def _validate_status(status):
    if status not in VALID_STATUSES:
        raise ValidationError("Status inválido")
    return status


def _validate_priority(priority):
    if isinstance(priority, bool) or not isinstance(priority, int) or not PRIORITY_MIN <= priority <= PRIORITY_MAX:
        raise ValidationError(f"Prioridade deve ser entre {PRIORITY_MIN} e {PRIORITY_MAX}")
    return priority


def _validate_due_date(value, message):
    if not value:
        return None
    parsed = parse_date(value)
    if parsed is None:
        raise ValidationError(message)
    return parsed


def validate_new_task(data):
    _require_dict(data)
    if not data.get("title"):
        raise ValidationError("Título é obrigatório")

    fields = {
        "title": _validate_title(data["title"]),
        "description": data.get("description", ""),
        "status": _validate_status(data.get("status", STATUS_PENDING)),
        "priority": _validate_priority(data.get("priority", DEFAULT_PRIORITY)),
        "user_id": data.get("user_id"),
        "category_id": data.get("category_id"),
        "due_date": _validate_due_date(data.get("due_date"), "Formato de data inválido. Use YYYY-MM-DD"),
    }
    if data.get("tags"):
        fields["tags"] = data["tags"]
    return fields


def validate_task_update(data):
    """Retorna apenas os campos presentes no payload, já validados."""
    _require_dict(data)
    fields = {}
    if "title" in data:
        fields["title"] = _validate_title(data["title"])
    if "description" in data:
        fields["description"] = data["description"]
    if "status" in data:
        fields["status"] = _validate_status(data["status"])
    if "priority" in data:
        fields["priority"] = _validate_priority(data["priority"])
    for key in ("user_id", "category_id"):
        if key in data:
            fields[key] = data[key]
    if "due_date" in data:
        fields["due_date"] = _validate_due_date(data["due_date"], "Formato de data inválido")
    if "tags" in data:
        fields["tags"] = data["tags"]
    return fields


def _optional_int(args, key, message):
    value = args.get(key, "")
    if value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(message)


def validate_search(args):
    return {
        "text": args.get("q", ""),
        "status": args.get("status", ""),
        "priority": _optional_int(args, "priority", "Prioridade inválida"),
        "user_id": _optional_int(args, "user_id", "user_id inválido"),
    }
