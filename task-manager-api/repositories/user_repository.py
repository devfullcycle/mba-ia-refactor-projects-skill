from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from database import db
from models.task import Task
from models.user import User


class UserRepository:
    """SQLAlchemy persistence operations for user use cases."""

    def __init__(self, session=None):
        self.session = db.session if session is None else session

    def get(self, user_id: int) -> User | None:
        return self.session.get(User, user_id)

    def get_by_id(self, user_id: int) -> User | None:
        return self.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return self.session.scalar(statement)

    def list_all(self) -> list[User]:
        return list(self.session.scalars(select(User)).all())

    def get_with_tasks(self, user_id: int) -> User | None:
        statement = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(self._tasks_relationship()))
        )
        return self.session.scalar(statement)

    def list_with_tasks(self) -> list[User]:
        statement = select(User).options(selectinload(self._tasks_relationship()))
        return list(self.session.scalars(statement).all())

    def list_with_task_counts(self) -> list[tuple[User, int]]:
        statement = (
            select(User, func.count(Task.id).label("task_count"))
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id)
        )
        return [
            (user, int(task_count))
            for user, task_count in self.session.execute(statement).all()
        ]

    def email_exists(self, email: str, *, excluding_user_id: int | None = None) -> bool:
        statement = select(User.id).where(User.email == email)
        if excluding_user_id is not None:
            statement = statement.where(User.id != excluding_user_id)
        return self.session.scalar(statement.limit(1)) is not None

    def add(self, user: User) -> User:
        self.session.add(user)
        return user

    def add_all(self, users: Iterable[User]) -> list[User]:
        user_list = list(users)
        self.session.add_all(user_list)
        return user_list

    def delete(self, user: User) -> None:
        self.session.delete(user)

    def delete_with_tasks(self, user: User) -> None:
        self.session.execute(delete(Task).where(Task.user_id == user.id))
        self.session.delete(user)

    def delete_all(self) -> int:
        result = self.session.execute(delete(User))
        return result.rowcount or 0

    def count(self) -> int:
        statement = select(func.count(User.id))
        return int(self.session.scalar(statement) or 0)

    @staticmethod
    def _tasks_relationship():
        # ``tasks`` is declared as a SQLAlchemy backref on Task.
        return User.__mapper__.relationships["tasks"].class_attribute
