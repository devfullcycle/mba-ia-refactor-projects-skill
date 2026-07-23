"""Validação e normalização de entradas, independente do transporte HTTP."""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import datetime
from typing import Any


VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
VALID_ROLES = ("user", "admin", "manager")
EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


class SchemaValidationError(ValueError):
    """Erro de entrada que pode ser traduzido pelo adapter para qualquer protocolo."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def _payload(data: Any) -> Mapping[str, Any]:
    if not isinstance(data, Mapping) or not data:
        raise SchemaValidationError("Dados inválidos")
    return data


def _integer(value: Any, message: str) -> int:
    if isinstance(value, bool):
        raise SchemaValidationError(message)
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise SchemaValidationError(message) from error


def _priority(value: Any) -> int:
    priority = _integer(value, "Prioridade inválida")
    if priority < 1 or priority > 5:
        raise SchemaValidationError("Prioridade deve ser entre 1 e 5")
    return priority


def _title(value: Any, *, required: bool) -> Any:
    if required and not value:
        raise SchemaValidationError("Título é obrigatório")
    if not isinstance(value, str):
        raise SchemaValidationError("Título inválido")
    if len(value) < 3:
        raise SchemaValidationError("Título muito curto")
    if len(value) > 200:
        raise SchemaValidationError("Título muito longo")
    return value


def _due_date(value: Any, message: str) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise SchemaValidationError(message)
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError as error:
        raise SchemaValidationError(message) from error


def _tags(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        if not all(isinstance(tag, str) for tag in value):
            raise SchemaValidationError("Tags inválidas")
        return ",".join(value)
    if not isinstance(value, str):
        raise SchemaValidationError("Tags inválidas")
    return value


def _optional_id(value: Any, message: str) -> int | None:
    if value is None or value == "":
        return None
    return _integer(value, message)


def validate_task_create(data: Any) -> dict[str, Any]:
    data = _payload(data)
    title = data.get("title")
    if not title:
        raise SchemaValidationError("Título é obrigatório")

    result = {
        "title": _title(title, required=True),
        "description": data.get("description", ""),
        "status": data.get("status", "pending"),
        "priority": _priority(data.get("priority", 3)),
        "user_id": _optional_id(data.get("user_id"), "Usuário inválido"),
        "category_id": _optional_id(data.get("category_id"), "Categoria inválida"),
        "due_date": _due_date(
            data.get("due_date"), "Formato de data inválido. Use YYYY-MM-DD"
        ),
        "tags": _tags(data.get("tags")),
    }
    if result["status"] not in VALID_STATUSES:
        raise SchemaValidationError("Status inválido")
    return result


def validate_task_update(data: Any) -> dict[str, Any]:
    data = _payload(data)
    result: dict[str, Any] = {}
    if "title" in data:
        result["title"] = _title(data["title"], required=False)
    if "description" in data:
        result["description"] = data["description"]
    if "status" in data:
        if data["status"] not in VALID_STATUSES:
            raise SchemaValidationError("Status inválido")
        result["status"] = data["status"]
    if "priority" in data:
        result["priority"] = _priority(data["priority"])
    if "user_id" in data:
        result["user_id"] = _optional_id(data["user_id"], "Usuário inválido")
    if "category_id" in data:
        result["category_id"] = _optional_id(
            data["category_id"], "Categoria inválida"
        )
    if "due_date" in data:
        result["due_date"] = _due_date(
            data["due_date"], "Formato de data inválido"
        )
    if "tags" in data:
        result["tags"] = _tags(data["tags"])
    return result


def validate_task_filters(data: Any) -> dict[str, Any]:
    if data is None:
        data = {}
    if not isinstance(data, Mapping):
        raise SchemaValidationError("Filtros inválidos")

    query = data.get("q", "")
    status = data.get("status", "")
    if query is None:
        query = ""
    if status is None:
        status = ""
    if not isinstance(query, str):
        raise SchemaValidationError("Busca inválida")
    if status and status not in VALID_STATUSES:
        raise SchemaValidationError("Status inválido")

    return {
        "q": query,
        "status": status,
        "priority": (
            _priority(data["priority"])
            if data.get("priority") not in (None, "")
            else None
        ),
        "user_id": (
            _integer(data["user_id"], "Usuário inválido")
            if data.get("user_id") not in (None, "")
            else None
        ),
    }


def validate_user_create(data: Any) -> dict[str, Any]:
    data = _payload(data)
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "user")

    if not name:
        raise SchemaValidationError("Nome é obrigatório")
    if not email:
        raise SchemaValidationError("Email é obrigatório")
    if not password:
        raise SchemaValidationError("Senha é obrigatória")
    if not isinstance(email, str) or EMAIL_PATTERN.match(email) is None:
        raise SchemaValidationError("Email inválido")
    if not isinstance(password, str) or len(password) < 4:
        raise SchemaValidationError("Senha deve ter no mínimo 4 caracteres")
    if role not in VALID_ROLES:
        raise SchemaValidationError("Role inválido")
    return {"name": name, "email": email, "password": password, "role": role}


def validate_user_update(data: Any) -> dict[str, Any]:
    data = _payload(data)
    result: dict[str, Any] = {}
    if "name" in data:
        result["name"] = data["name"]
    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or EMAIL_PATTERN.match(email) is None:
            raise SchemaValidationError("Email inválido")
        result["email"] = email
    if "password" in data:
        password = data["password"]
        if not isinstance(password, str) or len(password) < 4:
            raise SchemaValidationError("Senha muito curta")
        result["password"] = password
    if "role" in data:
        if data["role"] not in VALID_ROLES:
            raise SchemaValidationError("Role inválido")
        result["role"] = data["role"]
    if "active" in data:
        if not isinstance(data["active"], bool):
            raise SchemaValidationError("Ativo inválido")
        result["active"] = data["active"]
    return result


def validate_login(data: Any) -> dict[str, str]:
    data = _payload(data)
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise SchemaValidationError("Email e senha são obrigatórios")
    if not isinstance(email, str) or not isinstance(password, str):
        raise SchemaValidationError("Email e senha são obrigatórios")
    return {"email": email, "password": password}


def validate_category_create(data: Any) -> dict[str, Any]:
    data = _payload(data)
    name = data.get("name")
    if not name:
        raise SchemaValidationError("Nome é obrigatório")
    return {
        "name": name,
        "description": data.get("description", ""),
        "color": data.get("color", "#000000"),
    }


def validate_category_update(data: Any) -> dict[str, Any]:
    data = _payload(data)
    return {
        field: data[field]
        for field in ("name", "description", "color")
        if field in data
    }


# Nomes convenientes para adapters que selecionam create/update dinamicamente.
validate_search_filters = validate_task_filters


def validate_task_data(data: Any, *, partial: bool = False) -> dict[str, Any]:
    return validate_task_update(data) if partial else validate_task_create(data)


def validate_user_data(data: Any, *, partial: bool = False) -> dict[str, Any]:
    return validate_user_update(data) if partial else validate_user_create(data)


def validate_category_data(data: Any, *, partial: bool = False) -> dict[str, Any]:
    return validate_category_update(data) if partial else validate_category_create(data)
