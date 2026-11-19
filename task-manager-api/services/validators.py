from datetime import datetime

from database import db
from models.user import User
from models.category import Category
from utils.helpers import (
    VALID_STATUSES, MIN_TITLE_LENGTH, MAX_TITLE_LENGTH, MIN_PRIORITY, MAX_PRIORITY,
)


def validate_task_payload(data, partial=False):
    """Validação central de task (usada por create e update).

    Retorna (cleaned, error, status). `cleaned` traz os campos normalizados,
    incluindo `due_date_parsed` e `tags` já no formato de armazenamento.
    """
    if not data:
        return None, 'Dados inválidos', 400

    cleaned = {}

    title_required = not partial
    if 'title' in data or title_required:
        title = data.get('title')
        if not title:
            return None, 'Título é obrigatório', 400
        if len(title) < MIN_TITLE_LENGTH:
            return None, 'Título muito curto', 400
        if len(title) > MAX_TITLE_LENGTH:
            return None, 'Título muito longo', 400
        cleaned['title'] = title

    if 'description' in data:
        cleaned['description'] = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return None, 'Status inválido', 400
        cleaned['status'] = data['status']

    if 'priority' in data:
        if data['priority'] < MIN_PRIORITY or data['priority'] > MAX_PRIORITY:
            return None, 'Prioridade deve ser entre 1 e 5', 400
        cleaned['priority'] = data['priority']

    if 'user_id' in data:
        if data['user_id']:
            if not db.session.get(User, data['user_id']):
                return None, 'Usuário não encontrado', 404
        cleaned['user_id'] = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            if not db.session.get(Category, data['category_id']):
                return None, 'Categoria não encontrada', 404
        cleaned['category_id'] = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            try:
                cleaned['due_date_parsed'] = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                return None, 'Formato de data inválido. Use YYYY-MM-DD', 400
        else:
            cleaned['due_date_parsed'] = None

    if 'tags' in data:
        tags = data['tags']
        cleaned['tags'] = ','.join(tags) if isinstance(tags, list) else tags

    return cleaned, None, None
