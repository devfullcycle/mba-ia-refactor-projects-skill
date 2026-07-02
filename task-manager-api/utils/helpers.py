import logging
import re
import uuid
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


def utcnow():
    return datetime.now(UTC).replace(tzinfo=None)


def format_date(date_obj):
    if date_obj:
        return str(date_obj)
    return None


def calculate_percentage(part, total):
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email):
    if re.match(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$', email):
        return True
    return False


def sanitize_string(s):
    if s:
        return s.strip()
    return s


def generate_id():
    return str(uuid.uuid4())


def log_action(action, details=None):
    logger.info('ACTION: %s%s', action, f' | DETAILS: {details}' if details else '')


def parse_date(date_string):
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.strptime(date_string, '%d/%m/%Y')
        except ValueError:
            return None


def is_valid_color(color):
    if color and len(color) == 7 and color[0] == '#':
        return True
    return False


VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']
MAX_TITLE_LENGTH = 200
MIN_TITLE_LENGTH = 3
MIN_PASSWORD_LENGTH = 4
DEFAULT_PRIORITY = 3
DEFAULT_COLOR = '#000000'
