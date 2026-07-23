"""Schemas de entrada e presenters públicos da aplicação."""

from .presenters import (
    present_categories,
    present_category,
    present_error,
    present_health,
    present_index,
    present_login,
    present_message,
    present_public_user,
    present_summary_report,
    present_task,
    present_task_overdue,
    present_task_stats,
    present_task_with_relations,
    present_tasks,
    present_user,
    present_user_detail,
    present_user_list_item,
    present_user_report,
    present_user_task,
    present_user_tasks,
    present_users,
)
from .validators import (
    EMAIL_PATTERN,
    VALID_ROLES,
    VALID_STATUSES,
    SchemaValidationError,
    validate_category_create,
    validate_category_data,
    validate_category_update,
    validate_login,
    validate_search_filters,
    validate_task_create,
    validate_task_data,
    validate_task_filters,
    validate_task_update,
    validate_user_create,
    validate_user_data,
    validate_user_update,
)

__all__ = [name for name in globals() if name.startswith(("present_", "validate_"))]
__all__ += ["EMAIL_PATTERN", "VALID_ROLES", "VALID_STATUSES", "SchemaValidationError"]
