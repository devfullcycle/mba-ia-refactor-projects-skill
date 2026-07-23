from __future__ import annotations

from errors import NotFoundError
from models.task import Task
from schemas.validators import (
    validate_task_create,
    validate_task_filters,
    validate_task_update,
)
from services.clock import utc_now

from controllers.base import validate


class TaskController:
    def __init__(self, tasks, users, categories, session, clock=utc_now):
        self.tasks = tasks
        self.users = users
        self.categories = categories
        self.session = session
        self.clock = clock

    def list(self):
        return self.tasks.list_with_relations()

    def get(self, task_id):
        task = self.tasks.get(task_id)
        if task is None:
            raise NotFoundError("Task não encontrada")
        return task

    def create(self, payload):
        data = validate(validate_task_create, payload)
        self._validate_relations(data)
        task = Task(**data)
        self.tasks.add(task)
        self.session.commit()
        return task

    def update(self, task_id, payload):
        task = self.get(task_id)
        data = validate(validate_task_update, payload)
        self._validate_relations(data)
        for field, value in data.items():
            setattr(task, field, value)
        task.updated_at = self.clock()
        self.session.commit()
        return task

    def delete(self, task_id):
        task = self.get(task_id)
        self.tasks.delete(task)
        self.session.commit()

    def search(self, raw_filters):
        filters = validate(validate_task_filters, raw_filters)
        return self.tasks.search(
            query=filters["q"],
            status=filters["status"],
            priority=filters["priority"],
            user_id=filters["user_id"],
        )

    def stats(self):
        stats = self.tasks.statistics(self.clock())
        total = stats["total"]
        stats["completion_rate"] = (
            round((stats["done"] / total) * 100, 2) if total else 0
        )
        return stats

    def _validate_relations(self, data):
        user_id = data.get("user_id")
        if user_id is not None and self.users.get(user_id) is None:
            raise NotFoundError("Usuário não encontrado")
        category_id = data.get("category_id")
        if category_id is not None and self.categories.get(category_id) is None:
            raise NotFoundError("Categoria não encontrada")
