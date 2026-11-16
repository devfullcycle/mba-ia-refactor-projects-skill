"""Validação de entrada de Task. Devolve apenas campos limpos; erros viram ValidationError (400)."""
from datetime import datetime

from utils.constants import (
    DEFAULT_PRIORITY, DEFAULT_STATUS, MAX_TITLE_LENGTH, MIN_TITLE_LENGTH,
    PRIORITY_MAX, PRIORITY_MIN, TASK_STATUSES,
)
from utils.errors import ValidationError

DATE_FORMAT = '%Y-%m-%d'


def _title(value):
    if not isinstance(value, str):
        raise ValidationError('Título inválido')
    if len(value) < MIN_TITLE_LENGTH:
        raise ValidationError('Título muito curto')
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError('Título muito longo')
    return value


def _status(value):
    if not isinstance(value, str) or value not in TASK_STATUSES:
        raise ValidationError('Status inválido')
    return value


def _priority(value):
    valid = isinstance(value, int) and not isinstance(value, bool)
    if not valid or value < PRIORITY_MIN or value > PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')
    return value


def _foreign_id(value, field):
    if value and (not isinstance(value, int) or isinstance(value, bool)):
        raise ValidationError(f'{field} inválido')
    return value or None


def _due_date(value, message):
    if not value:
        return None
    try:
        return datetime.strptime(value, DATE_FORMAT)
    except (ValueError, TypeError):
        raise ValidationError(message)


def _tags(value):
    if isinstance(value, list):
        if not all(isinstance(t, str) for t in value):
            raise ValidationError('Tags inválidas')
        return ','.join(value)
    if value is not None and not isinstance(value, str):
        raise ValidationError('Tags inválidas')
    return value


def validate_create(data):
    title = data.get('title')
    if not title:
        raise ValidationError('Título é obrigatório')
    fields = {'title': _title(title)}
    fields['description'] = data.get('description', '')
    fields['status'] = _status(data.get('status', DEFAULT_STATUS))
    fields['priority'] = _priority(data.get('priority', DEFAULT_PRIORITY))
    fields['user_id'] = _foreign_id(data.get('user_id'), 'user_id')
    fields['category_id'] = _foreign_id(data.get('category_id'), 'category_id')
    fields['due_date'] = _due_date(
        data.get('due_date'), 'Formato de data inválido. Use YYYY-MM-DD')
    fields['tags'] = _tags(data.get('tags')) or None
    return fields


def validate_update(data):
    fields = {}
    if 'title' in data:
        fields['title'] = _title(data['title'])
    if 'description' in data:
        fields['description'] = data['description']
    if 'status' in data:
        fields['status'] = _status(data['status'])
    if 'priority' in data:
        fields['priority'] = _priority(data['priority'])
    if 'user_id' in data:
        fields['user_id'] = _foreign_id(data['user_id'], 'user_id')
    if 'category_id' in data:
        fields['category_id'] = _foreign_id(data['category_id'], 'category_id')
    if 'due_date' in data:
        fields['due_date'] = _due_date(data['due_date'], 'Formato de data inválido')
    if 'tags' in data:
        fields['tags'] = _tags(data['tags'])
    return fields


def parse_search_filters(args):
    """Filtros de /tasks/search; priority e user_id precisam ser inteiros."""
    filters = {
        'q': args.get('q', ''),
        'status': args.get('status', ''),
        'priority': None,
        'user_id': None,
    }
    for key, message in (('priority', 'Prioridade inválida'), ('user_id', 'user_id inválido')):
        raw = args.get(key, '')
        if raw:
            try:
                filters[key] = int(raw)
            except ValueError:
                raise ValidationError(message)
    return filters
