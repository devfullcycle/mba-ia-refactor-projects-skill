"""Constantes de domínio e regras de validação (sem segredos, sem I/O)."""

# Status de task
STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'
STATUS_CANCELLED = 'cancelled'
VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
# Status que encerram a task (uma task nesses status nunca está atrasada)
CLOSED_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

# Prioridade (1 = mais alta)
PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
HIGH_PRIORITY_MAX = 2  # prioridades <= 2 contam como "alta"
PRIORITY_LABELS = {
    1: 'critical',
    2: 'high',
    3: 'medium',
    4: 'low',
    5: 'minimal',
}

# Título
MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200

# Usuários
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)
MIN_PASSWORD_LENGTH = 4
EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'

# Categorias
DEFAULT_COLOR = '#000000'
COLOR_LENGTH = 7  # '#rrggbb'

# Datas
DATE_FORMAT = '%Y-%m-%d'
RECENT_ACTIVITY_DAYS = 7
