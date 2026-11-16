import re

from utils.constants import COLOR_PATTERN, DEFAULT_COLOR
from utils.errors import ValidationError


def _name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError('Nome inválido')
    return value


def _color(value):
    if not isinstance(value, str) or not re.match(COLOR_PATTERN, value):
        raise ValidationError('Cor inválida. Use o formato #RRGGBB')
    return value


def validate_create(data):
    name = data.get('name')
    if not name:
        raise ValidationError('Nome é obrigatório')
    return {
        'name': _name(name),
        'description': data.get('description', ''),
        'color': _color(data.get('color', DEFAULT_COLOR)),
    }


def validate_update(data):
    fields = {}
    if 'name' in data:
        fields['name'] = _name(data['name'])
    if 'description' in data:
        fields['description'] = data['description']
    if 'color' in data:
        fields['color'] = _color(data['color'])
    return fields
