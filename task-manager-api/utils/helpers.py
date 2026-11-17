import logging
import re
import uuid
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Constantes de validação e domínio
VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'

def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None

def calculate_percentage(part, total):
    if not total:
        return 0.0
    return round((part / total) * 100, 2)

def validate_email(email):
    if not email:
        return False
    return bool(re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email))

def sanitize_string(s):
    if s:
        return s.strip()
    return s

def generate_id():
    return str(uuid.uuid4())

def log_action(action, details=None):
    timestamp = datetime.now(timezone.utc)
    logger.info(f"[{timestamp}] ACTION: {action} | DETAILS: {details or 'N/A'}")

def parse_date(date_string):
    if not date_string:
        return None
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    return None

def is_valid_color(color):
    return bool(color and len(color) == 7 and color.startswith('#'))

def process_task_data(data, existing_task=None):
    result = {}

    if 'title' in data:
        title = sanitize_string(data.get('title'))
        if not title:
            return None, 'Título não pode ser vazio'
        if not (MIN_TITLE_LENGTH <= len(title) <= MAX_TITLE_LENGTH):
            return None, f'Título deve ter entre {MIN_TITLE_LENGTH} e {MAX_TITLE_LENGTH} caracteres'
        result['title'] = title

    if 'description' in data:
        result['description'] = data.get('description', '')

    if 'status' in data:
        status = data.get('status')
        if status not in VALID_STATUSES:
            return None, 'Status inválido'
        result['status'] = status

    if 'priority' in data:
        try:
            p = int(data['priority'])
            if not (1 <= p <= 5):
                return None, 'Prioridade deve ser entre 1 e 5'
            result['priority'] = p
        except (ValueError, TypeError):
            return None, 'Prioridade inválida'

    if 'due_date' in data:
        due_val = data.get('due_date')
        if due_val:
            parsed = parse_date(due_val)
            if not parsed:
                return None, 'Data inválida'
            result['due_date'] = parsed
        else:
            result['due_date'] = None

    if 'tags' in data:
        tags = data.get('tags')
        if isinstance(tags, list):
            result['tags'] = ','.join(str(tag).strip() for tag in tags if tag)
        else:
            result['tags'] = str(tags) if tags else None

    return result, None
