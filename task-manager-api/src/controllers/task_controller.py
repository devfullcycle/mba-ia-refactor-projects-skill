"""Task use cases: CRUD, search and statistics."""
import logging

from src.controllers import validators
from src.controllers.errors import NotFoundError
from src.controllers.metrics import completion_rate
from src.models.constants import VALID_STATUSES, STATUS_DONE
from src.models.database import utcnow

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, tasks, users, categories, clock=utcnow):
        self.tasks = tasks
        self.users = users
        self.categories = categories
        self.clock = clock

    def list_tasks(self):
        return self.tasks.list_with_relations()

    def get_task(self, task_id):
        task = self.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task não encontrada")
        return task

    def _ensure_references(self, fields):
        if fields.get("user_id") and self.users.get(fields["user_id"]) is None:
            raise NotFoundError("Usuário não encontrado")
        if fields.get("category_id") and self.categories.get(fields["category_id"]) is None:
            raise NotFoundError("Categoria não encontrada")

    def create_task(self, data):
        fields = validators.parse_task_create(data)
        self._ensure_references(fields)
        task = self.tasks.new(**fields)
        self.tasks.commit()
        logger.info("Task criada id=%s", task.id)
        return task

    def update_task(self, task_id, data):
        task = self.get_task(task_id)
        fields = validators.parse_task_update(data)
        self._ensure_references(fields)
        for name, value in fields.items():
            setattr(task, name, value)
        task.updated_at = self.clock()
        self.tasks.commit()
        logger.info("Task atualizada id=%s", task.id)
        return task

    def delete_task(self, task_id):
        task = self.get_task(task_id)
        self.tasks.delete(task)
        self.tasks.commit()
        logger.info("Task deletada id=%s", task_id)

    def search(self, args):
        return self.tasks.search(**validators.parse_search_filters(args))

    def stats(self):
        by_status = self.tasks.count_by_status()
        total = self.tasks.count()
        stats = {status: by_status.get(status, 0) for status in VALID_STATUSES}
        stats.update(
            total=total,
            overdue=self.tasks.count_overdue(self.clock()),
            completion_rate=completion_rate(by_status.get(STATUS_DONE, 0), total),
        )
        return stats
