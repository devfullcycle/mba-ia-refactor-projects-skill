import logging

from src.controllers import validators
from src.controllers.errors import NotFoundError
from src.controllers.metrics import completion_rate
from src.models.database import utcnow
from src.models.task_model import DEFAULT_PRIORITY, STATUS_PENDING, Task

logger = logging.getLogger(__name__)

TASK_NOT_FOUND = "Task não encontrada"
USER_NOT_FOUND = "Usuário não encontrado"
CATEGORY_NOT_FOUND = "Categoria não encontrada"


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
            raise NotFoundError(TASK_NOT_FOUND)
        return task

    def search_tasks(self, text, status, priority, user_id):
        return self.tasks.search(
            text=text,
            status=status,
            priority=validators.parse_int_query(priority, "Prioridade inválida"),
            user_id=validators.parse_int_query(user_id, "Usuário inválido"),
        )

    def stats(self):
        by_status = self.tasks.count_by_status()
        total = self.tasks.count()
        now = utcnow()
        overdue = sum(1 for task in self.tasks.list_all() if task.is_overdue(now))
        return {
            "total": total,
            **by_status,
            "overdue": overdue,
            "completion_rate": completion_rate(by_status["done"], total),
        }

    def create_task(self, data):
        data = validators.require_body(data)
        title = validators.validate_title(data.get("title"))
        status = validators.validate_status(data.get("status", STATUS_PENDING))
        priority = validators.validate_priority(data.get("priority", DEFAULT_PRIORITY))
        user_id = self._existing_user_id(data.get("user_id"))
        category_id = self._existing_category_id(data.get("category_id"))
        due_date = None
        if data.get("due_date"):
            due_date = validators.parse_due_date(data["due_date"], "Formato de data inválido. Use YYYY-MM-DD")
        tags = validators.normalize_tags(data["tags"]) if data.get("tags") else None

        task = Task(
            title=title, description=data.get("description", ""), status=status, priority=priority,
            user_id=user_id, category_id=category_id, due_date=due_date, tags=tags,
        )
        self.tasks.add(task)
        self.tasks.commit()
        logger.info("Task criada id=%s", task.id)
        return task

    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        data = validators.require_body(data)
        changes = {}
        if "title" in data:
            changes["title"] = validators.validate_title(data["title"], required=False)
        if "description" in data:
            changes["description"] = data["description"]
        if "status" in data:
            changes["status"] = validators.validate_status(data["status"])
        if "priority" in data:
            changes["priority"] = validators.validate_priority(data["priority"])
        if "user_id" in data:
            changes["user_id"] = self._existing_user_id(data["user_id"])
        if "category_id" in data:
            changes["category_id"] = self._existing_category_id(data["category_id"])
        if "due_date" in data:
            due_date = data["due_date"]
            changes["due_date"] = (
                validators.parse_due_date(due_date, "Formato de data inválido") if due_date else None
            )
        if "tags" in data:
            changes["tags"] = validators.normalize_tags(data["tags"])

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

    def _existing_user_id(self, raw_id):
        if not raw_id:
            return None
        user_id = validators.coerce_id(raw_id)
        if user_id is None or self.users.get(user_id) is None:
            raise NotFoundError(USER_NOT_FOUND)
        return user_id

    def _existing_category_id(self, raw_id):
        if not raw_id:
            return None
        category_id = validators.coerce_id(raw_id)
        if category_id is None or self.categories.get(category_id) is None:
            raise NotFoundError(CATEGORY_NOT_FOUND)
        return category_id
