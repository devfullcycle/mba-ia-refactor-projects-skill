from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, func, select

from database import db
from models.category import Category
from models.task import Task
from models.user import User


class SeedRepository:
    """Bulk data access used by the seed use case.

    The caller owns the surrounding transaction. This repository deliberately
    contains neither commits nor built-in users, passwords, or other seed data.
    """

    def __init__(self, session=None):
        self.session = db.session if session is None else session

    def reset(self) -> None:
        self.session.execute(delete(Task))
        self.session.execute(delete(User))
        self.session.execute(delete(Category))

    def add_users(self, users: Iterable[User], *, flush: bool = False) -> list[User]:
        user_list = list(users)
        self.session.add_all(user_list)
        if flush:
            self.session.flush()
        return user_list

    def add_categories(
        self,
        categories: Iterable[Category],
        *,
        flush: bool = False,
    ) -> list[Category]:
        category_list = list(categories)
        self.session.add_all(category_list)
        if flush:
            self.session.flush()
        return category_list

    def add_tasks(self, tasks: Iterable[Task], *, flush: bool = False) -> list[Task]:
        task_list = list(tasks)
        self.session.add_all(task_list)
        if flush:
            self.session.flush()
        return task_list

    def populate(
        self,
        *,
        users: Iterable[User],
        categories: Iterable[Category],
        tasks: Iterable[Task],
        flush: bool = False,
    ) -> None:
        self.add_users(users)
        self.add_categories(categories)
        self.add_tasks(tasks)
        if flush:
            self.session.flush()

    def replace_all(
        self,
        *,
        users: Iterable[User],
        categories: Iterable[Category],
        tasks: Iterable[Task],
        flush: bool = False,
    ) -> None:
        self.reset()
        self.populate(
            users=users,
            categories=categories,
            tasks=tasks,
            flush=flush,
        )

    def flush(self) -> None:
        self.session.flush()

    def counts(self) -> dict[str, int]:
        statement = select(
            select(func.count(User.id)).scalar_subquery().label("users"),
            select(func.count(Category.id)).scalar_subquery().label("categories"),
            select(func.count(Task.id)).scalar_subquery().label("tasks"),
        )
        row = self.session.execute(statement).one()
        return {key: int(value or 0) for key, value in row._mapping.items()}
