"""Constantes de domínio (evita literais espalhados)."""

API_VERSION = '1.0'

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
TASK_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
DEFAULT_STATUS = STATUS_PENDING
FINISHED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

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

ADMIN_ROLE = 'admin'
MANAGER_ROLE = 'manager'
DEFAULT_ROLE = 'user'
USER_ROLES = (DEFAULT_ROLE, ADMIN_ROLE, MANAGER_ROLE)
STAFF_ROLES = (ADMIN_ROLE, MANAGER_ROLE)  # podem gerenciar tasks de qualquer usuário
PRIVILEGED_USER_FIELDS = frozenset({'role', 'active'})  # só admin define/altera

# Vale para senhas novas; senhas já cadastradas continuam aceitas no login.
MIN_PASSWORD_LENGTH = 8

# Limites alinhados ao tamanho das colunas (o SQLite não os aplica sozinho).
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 150
MAX_CATEGORY_DESCRIPTION_LENGTH = 300
MAX_TASK_DESCRIPTION_LENGTH = 5000
MAX_TAGS_LENGTH = 500

DEFAULT_COLOR = '#000000'
EMAIL_PATTERN = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
COLOR_PATTERN = r'^#[0-9a-fA-F]{6}$'

RECENT_DAYS = 7

# Paginação opcional (?limit=&offset=); sem limit, a listagem é completa como antes.
MAX_PAGE_SIZE = 100
