"""Constantes de domínio centralizadas (fim dos magic strings/numbers)."""

VALID_STATUSES = ['pending', 'in_progress', 'done', 'cancelled']
VALID_ROLES = ['user', 'admin', 'manager']

MIN_TITLE_LENGTH = 3
MAX_TITLE_LENGTH = 200
MIN_PASSWORD_LENGTH = 4

MIN_PRIORITY = 1
MAX_PRIORITY = 5
DEFAULT_PRIORITY = 3

DEFAULT_COLOR = '#000000'
DATE_FORMAT = '%Y-%m-%d'

# status que "encerram" a task e portanto nunca contam como atrasadas.
CLOSED_STATUSES = ['done', 'cancelled']
