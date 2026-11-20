"""Task use cases: CRUD, search and statistics."""
import logging

from ..models.task_model import DEFAULT_PRIORITY, STATUS_DONE, STATUS_PENDING, TASK_STATUSES, Task
from ..models.database import utcnow
from . import validators
from .errors import NotFoundError
from .metrics import completion_rate

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, tasks, users, categories):
        self.tasks = tasks
        self.users = users
        self.categories = categories

    def list_tasks(self):
        return self.tasks.list_with_relations()

    def get_task(self, task_id):
        task = self.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task não encontrada")
        return task

    def create_task(self, data):
        validators.require_payload(data)
        task = Task(
            title=validators.validate_title(data.get("title")),
            status=validators.validate_status(data.get("status", STATUS_PENDING)),
            priority=validators.validate_priority(data.get("priority", DEFAULT_PRIORITY)),
            user_id=self._existing_user_id(data.get("user_id")),
            category_id=self._existing_category_id(data.get("category_id")),
            due_date=validators.parse_due_date(data.get("due_date")),
            tags=validators.normalize_tags(data.get("tags")),
            description=validators.optional_text(data.get("description", ""), "Descrição inválida"),
        )
        self.tasks.add(task)
        self.tasks.commit()
        logger.info("Task criada id=%s", task.id)
        return task

    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        validators.require_payload(data)
        changes = self._validated_changes(data)
        for field, value in changes.items():
            setattr(task, field, value)
        task.updated_at = utcnow()
        self.tasks.commit()
        logger.info("Task atualizada id=%s", task.id)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        self.tasks.delete(task)
        self.tasks.commit()
        logger.info("Task deletada id=%s", task_id)

    def search_tasks(self, text, status, priority, user_id):
        return self.tasks.search(
            text=text,
            status=status,
            priority=validators.parse_int_query(priority, validators.MSG_INVALID_PRIORITY),
            user_id=validators.parse_int_query(user_id, "Usuário inválido"),
        )

    def stats(self):
        total = self.tasks.count()
        by_status = self.tasks.count_by_status()
        result = {status: by_status.get(status, 0) for status in TASK_STATUSES}
        result["total"] = total
        result["overdue"] = self.tasks.count_overdue(utcnow())
        result["completion_rate"] = completion_rate(result[STATUS_DONE], total)
        return result

    def _validated_changes(self, data):
        """Validate every provided field before touching the entity (all-or-nothing update)."""
        rules = {
            "title": validators.validate_title,
            "description": lambda value: validators.optional_text(value, "Descrição inválida"),
            "status": validators.validate_status,
            "priority": validators.validate_priority,
            "user_id": self._existing_user_id,
            "category_id": self._existing_category_id,
            "due_date": validators.parse_due_date,
            "tags": validators.normalize_tags,
        }
        return {field: rule(data[field]) for field, rule in rules.items() if field in data}

    def _existing_user_id(self, value):
        user_id = validators.parse_optional_id(value, "Usuário inválido")
        if user_id is not None and self.users.get(user_id) is None:
            raise NotFoundError("Usuário não encontrado")
        return user_id

    def _existing_category_id(self, value):
        category_id = validators.parse_optional_id(value, "Categoria inválida")
        if category_id is not None and self.categories.get(category_id) is None:
            raise NotFoundError("Categoria não encontrada")
        return category_id
