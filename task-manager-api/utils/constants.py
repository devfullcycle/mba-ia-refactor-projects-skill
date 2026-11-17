"""Constantes de domínio (evita literais espalhados)."""

TASK_STATUSES = ('pending', 'in_progress', 'done', 'cancelled')
DEFAULT_STATUS = 'pending'
FINISHED_STATUSES = ('done', 'cancelled')

PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades 1 e 2 contam como "alta"
PRIORITY_LABELS = {
    1: 'critical',
    2: 'high',
    3: 'medium',
    4: 'low',
    5: 'minimal',
}

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

USER_ROLES = ('user', 'admin', 'manager')
DEFAULT_ROLE = 'user'
ADMIN_ROLE = 'admin'
MIN_PASSWORD_LENGTH = 4

DEFAULT_COLOR = '#000000'
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
COLOR_PATTERN = r'^#[0-9a-fA-F]{6}$'

RECENT_DAYS = 7
