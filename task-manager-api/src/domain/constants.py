"""Constantes de domínio.

Fonte única de verdade para os valores que o legado repetia em literais espalhados por
`routes/` e duplicava em `utils/helpers.py` (onde as constantes existiam e nunca eram usadas).
"""

# Status de tarefa
STATUS_PENDING = "pending"
STATUS_IN_PROGRESS = "in_progress"
STATUS_DONE = "done"
STATUS_CANCELLED = "cancelled"

VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE, STATUS_CANCELLED)
# Status que encerram a tarefa: uma vez neles, ela não conta como atrasada.
TERMINAL_STATUSES = (STATUS_DONE, STATUS_CANCELLED)

# Papéis de usuário
ROLE_USER = "user"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
VALID_ROLES = (ROLE_USER, ROLE_ADMIN, ROLE_MANAGER)

# Tarefa
TITLE_MIN_LENGTH = 3
TITLE_MAX_LENGTH = 200
PRIORITY_MIN = 1
PRIORITY_MAX = 5
DEFAULT_PRIORITY = 3
# Prioridade numérica considerada "alta" nos relatórios
HIGH_PRIORITY_THRESHOLD = 2
PRIORITY_LABELS = {1: "critical", 2: "high", 3: "medium", 4: "low", 5: "minimal"}

# Categoria
DEFAULT_COLOR = "#000000"
COLOR_LENGTH = 7

# Relatórios
RECENT_ACTIVITY_DAYS = 7

# Formatos de data aceitos na entrada
DATE_INPUT_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")
