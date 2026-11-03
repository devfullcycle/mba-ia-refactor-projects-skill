"""Fluxo dos casos de uso de Task."""
import logging

from models.category import Category
from models.task import STATUS_CANCELLED, STATUS_DONE, STATUS_IN_PROGRESS, STATUS_PENDING, Task, completion_rate
from models.user import User
from utils.clock import utcnow
from utils.errors import NotFoundError
from validators.task_validator import validate_new_task, validate_search, validate_task_update

logger = logging.getLogger(__name__)


class TaskController:
    def __init__(self, session, notification_service):
        self._session = session
        self._notifications = notification_service

    def _get_or_404(self, task_id):
        task = Task.get(task_id)
        if not task:
            raise NotFoundError("Task não encontrada")
        return task

    @staticmethod
    def _ensure_references(user_id=None, category_id=None):
        user = User.get(user_id) if user_id else None
        if user_id and not user:
            raise NotFoundError("Usuário não encontrado")
        if category_id and not Category.get(category_id):
            raise NotFoundError("Categoria não encontrada")
        return user

    def list_tasks(self):
        now = utcnow()
        return [task.to_list_item(now) for task in Task.list_with_relations()]

    def get_task(self, task_id):
        return self._get_or_404(task_id).to_detail_dict()

    def create_task(self, data):
        fields = validate_new_task(data)
        assignee = self._ensure_references(fields["user_id"], fields["category_id"])

        task = Task()
        tags = fields.pop("tags", None)
        for key, value in fields.items():
            setattr(task, key, value)
        if tags:
            task.set_tags(tags)

        self._session.add(task)
        self._session.commit()
        logger.info("Task criada: %s - %s", task.id, task.title)
        if assignee:
            self._notifications.notify_task_assigned(assignee, task)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self._get_or_404(task_id)
        fields = validate_task_update(data)
        new_assignee = self._ensure_references(fields.get("user_id"), fields.get("category_id"))
        previous_user_id = task.user_id

        tags_present = "tags" in fields
        tags = fields.pop("tags", None)
        for key, value in fields.items():
            setattr(task, key, value)
        if tags_present:
            task.set_tags(tags)
        task.updated_at = utcnow()

        self._session.commit()
        logger.info("Task atualizada: %s", task.id)
        if new_assignee and new_assignee.id != previous_user_id:
            self._notifications.notify_task_assigned(new_assignee, task)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self._get_or_404(task_id)
        self._session.delete(task)
        self._session.commit()
        logger.info("Task deletada: %s", task_id)

    def search(self, args):
        return [task.to_dict() for task in Task.search(**validate_search(args))]

    def stats(self):
        total = Task.count()
        by_status = Task.count_by(Task.status)
        done = by_status.get(STATUS_DONE, 0)
        return {
            "total": total,
            "pending": by_status.get(STATUS_PENDING, 0),
            "in_progress": by_status.get(STATUS_IN_PROGRESS, 0),
            "done": done,
            "cancelled": by_status.get(STATUS_CANCELLED, 0),
            "overdue": len(Task.overdue()),
            "completion_rate": completion_rate(done, total),
        }
