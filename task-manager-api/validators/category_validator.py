"""Validação de entrada de Categoria."""
from models.category import DEFAULT_COLOR, is_valid_color
from utils.errors import ValidationError


def _require_dict(data):
    if not data or not isinstance(data, dict):
        raise ValidationError("Dados inválidos")


def _validate_color(color):
    if not is_valid_color(color):
        raise ValidationError("Cor inválida. Use o formato #RRGGBB")
    return color


def validate_new_category(data):
    _require_dict(data)
    if not data.get("name"):
        raise ValidationError("Nome é obrigatório")
    return {
        "name": data["name"],
        "description": data.get("description", ""),
        "color": _validate_color(data.get("color", DEFAULT_COLOR)),
    }


def validate_category_update(data):
    _require_dict(data)
    fields = {}
    if "name" in data:
        if not data["name"]:
            raise ValidationError("Nome é obrigatório")
        fields["name"] = data["name"]
    if "description" in data:
        fields["description"] = data["description"]
    if "color" in data:
        fields["color"] = _validate_color(data["color"])
    return fields
