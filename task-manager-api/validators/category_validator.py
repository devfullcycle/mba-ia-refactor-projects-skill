import re

from utils.constants import COLOR_PATTERN, DEFAULT_COLOR, MAX_CATEGORY_DESCRIPTION_LENGTH
from utils.errors import ValidationError
from validators import common

_DESCRIPTION_MESSAGE = f'Descrição inválida (texto de até {MAX_CATEGORY_DESCRIPTION_LENGTH} caracteres)'


def _color(value):
    if not isinstance(value, str) or not re.match(COLOR_PATTERN, value):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return value


def _description(value):
    return common.optional_text(value, MAX_CATEGORY_DESCRIPTION_LENGTH, _DESCRIPTION_MESSAGE)


def validate_create(data):
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return {
        'name': common.name(name),
        'description': _description(data.get('description', '')),
        'color': _color(data.get('color', DEFAULT_COLOR)),
    }


def validate_update(data):
    fields = {}
    if 'name' in data:
        fields['name'] = common.name(data['name'])
    if 'description' in data:
        fields['description'] = _description(data['description'])
    if 'color' in data:
        fields['color'] = _color(data['color'])
    return fields
