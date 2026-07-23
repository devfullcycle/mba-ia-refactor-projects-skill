from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from sqlalchemy import and_, case, delete, func, or_, select
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User


class TaskRepository:
    """SQLAlchemy persistence operations for task use cases.

    Transaction boundaries deliberately belong to the caller. No method commits
    or rolls back the session.
    """

    def __init__(self, session=None):
        self.session = db.session if session is None else session

    def get(self, task_id: int) -> Task | None:
        return self.session.get(Task, task_id)

    def get_by_id(self, task_id: int) -> Task | None:
        return self.get(task_id)

    def list_all(self) -> list[Task]:
        return list(self.session.scalars(select(Task)).all())

    def list_with_relations(self) -> list[Task]:
        statement = select(Task).options(
            joinedload(Task.user),
            joinedload(Task.category),
        )
        return list(self.session.scalars(statement).all())

    def list_by_user(self, user_id: int) -> list[Task]:
        statement = select(Task).where(Task.user_id == user_id)
        return list(self.session.scalars(statement).all())

    def search(
        self,
        *,
        query: str = "",
        status: str | None = None,
        priority: int | None = None,
        user_id: int | None = None,
        with_relations: bool = False,
    ) -> list[Task]:
        statement = select(Task)
        if with_relations:
            statement = statement.options(
                joinedload(Task.user),
                joinedload(Task.category),
            )
        if query:
            pattern = f"%{query}%"
            statement = statement.where(
                or_(Task.title.like(pattern), Task.description.like(pattern))
            )
        if status:
            statement = statement.where(Task.status == status)
        if priority is not None:
            statement = statement.where(Task.priority == priority)
        if user_id is not None:
            statement = statement.where(Task.user_id == user_id)
        return list(self.session.scalars(statement).all())

    def add(self, task: Task) -> Task:
        self.session.add(task)
        return task

    def add_all(self, tasks: Iterable[Task]) -> list[Task]:
        task_list = list(tasks)
        self.session.add_all(task_list)
        return task_list

    def delete(self, task: Task) -> None:
        self.session.delete(task)

    def delete_all(self) -> int:
        result = self.session.execute(delete(Task))
        return result.rowcount or 0

    def delete_by_user(self, user_id: int) -> int:
        result = self.session.execute(delete(Task).where(Task.user_id == user_id))
        return result.rowcount or 0

    def count(self) -> int:
        statement = select(func.count(Task.id))
        return int(self.session.scalar(statement) or 0)

    def counts_by_status(self) -> dict[str, int]:
        statement = select(Task.status, func.count(Task.id)).group_by(Task.status)
        return {
            status: int(total)
            for status, total in self.session.execute(statement).all()
        }

    def counts_by_priority(self) -> dict[int, int]:
        statement = select(Task.priority, func.count(Task.id)).group_by(Task.priority)
        return {
            priority: int(total)
            for priority, total in self.session.execute(statement).all()
        }

    def list_overdue(self, now: datetime) -> list[Task]:
        statement = select(Task).where(self._overdue_condition(now))
        return list(self.session.scalars(statement).all())

    def count_overdue(self, now: datetime) -> int:
        statement = select(func.count(Task.id)).where(self._overdue_condition(now))
        return int(self.session.scalar(statement) or 0)

    def statistics(self, now: datetime) -> dict[str, int]:
        statement = select(
            func.count(Task.id).label("total"),
            self._conditional_count(Task.status == "pending").label("pending"),
            self._conditional_count(Task.status == "in_progress").label(
                "in_progress"
            ),
            self._conditional_count(Task.status == "done").label("done"),
            self._conditional_count(Task.status == "cancelled").label("cancelled"),
            self._conditional_count(self._overdue_condition(now)).label("overdue"),
        )
        row = self.session.execute(statement).one()
        return {key: int(value or 0) for key, value in row._mapping.items()}

    def user_statistics(self, user_id: int, now: datetime) -> dict[str, int]:
        statement = select(
            func.count(Task.id).label("total_tasks"),
            self._conditional_count(Task.status == "done").label("done"),
            self._conditional_count(Task.status == "pending").label("pending"),
            self._conditional_count(Task.status == "in_progress").label(
                "in_progress"
            ),
            self._conditional_count(Task.status == "cancelled").label("cancelled"),
            self._conditional_count(self._overdue_condition(now)).label("overdue"),
            self._conditional_count(Task.priority <= 2).label("high_priority"),
        ).where(Task.user_id == user_id)
        row = self.session.execute(statement).one()
        return {key: int(value or 0) for key, value in row._mapping.items()}

    def recent_activity(self, since: datetime) -> dict[str, int]:
        statement = select(
            self._conditional_count(Task.created_at >= since).label("created"),
            self._conditional_count(
                and_(Task.status == "done", Task.updated_at >= since)
            ).label("completed"),
        )
        row = self.session.execute(statement).one()
        return {key: int(value or 0) for key, value in row._mapping.items()}

    def productivity_by_user(self) -> list[dict[str, int | str]]:
        statement = (
            select(
                User.id.label("user_id"),
                User.name.label("user_name"),
                func.count(Task.id).label("total_tasks"),
                self._conditional_count(Task.status == "done").label(
                    "completed_tasks"
                ),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id, User.name)
        )
        return [dict(row._mapping) for row in self.session.execute(statement).all()]

    @staticmethod
    def _conditional_count(condition):
        return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)

    @staticmethod
    def _overdue_condition(now: datetime):
        return and_(
            Task.due_date.is_not(None),
            Task.due_date < now,
            Task.status.not_in(("done", "cancelled")),
        )
