"""Validação de Categoria.

O legado não validava a cor em nenhum dos endpoints, apesar de existir `is_valid_color` em
`utils/helpers.py` — nunca chamada.
"""
import re

from src.domain.constants import DEFAULT_COLOR
from src.middlewares.error_handler import ValidationError

COLOR_REGEX = re.compile(r"^#[0-9a-fA-F]{6}$")


def _validate_color(valor):
    cor = str(valor or "")
    if not COLOR_REGEX.match(cor):
        raise ValidationError("Cor inválida. Use o formato #RRGGBB")
    return cor


def validate_category(dados, partial=False):
    if not dados:
        raise ValidationError("Dados inválidos")

    saida = {}

    if not partial or "name" in dados:
        nome = str(dados.get("name") or "").strip()
        if not nome:
            raise ValidationError("Nome é obrigatório")
        saida["name"] = nome

    if "description" in dados:
        saida["description"] = dados["description"]
    elif not partial:
        saida["description"] = dados.get("description", "")

    if "color" in dados:
        saida["color"] = _validate_color(dados["color"])
    elif not partial:
        saida["color"] = DEFAULT_COLOR

    return saida
