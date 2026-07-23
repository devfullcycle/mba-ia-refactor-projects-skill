from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import delete, func, select, update

from database import db
from models.category import Category
from models.task import Task


class CategoryRepository:
    """SQLAlchemy persistence operations for category use cases."""

    def __init__(self, session=None):
        self.session = db.session if session is None else session

    def get(self, category_id: int) -> Category | None:
        return self.session.get(Category, category_id)

    def get_by_id(self, category_id: int) -> Category | None:
        return self.get(category_id)

    def list_all(self) -> list[Category]:
        return list(self.session.scalars(select(Category)).all())

    def list_with_task_counts(self) -> list[tuple[Category, int]]:
        statement = (
            select(Category, func.count(Task.id).label("task_count"))
            .outerjoin(Task, Task.category_id == Category.id)
            .group_by(Category.id)
        )
        return [
            (category, int(task_count))
            for category, task_count in self.session.execute(statement).all()
        ]

    def add(self, category: Category) -> Category:
        self.session.add(category)
        return category

    def add_all(self, categories: Iterable[Category]) -> list[Category]:
        category_list = list(categories)
        self.session.add_all(category_list)
        return category_list

    def delete(self, category: Category) -> None:
        self.session.delete(category)

    def delete_and_detach_tasks(self, category: Category) -> None:
        self.session.execute(
            update(Task)
            .where(Task.category_id == category.id)
            .values(category_id=None)
        )
        self.session.delete(category)

    def delete_all(self) -> int:
        result = self.session.execute(delete(Category))
        return result.rowcount or 0

    def count(self) -> int:
        statement = select(func.count(Category.id))
        return int(self.session.scalar(statement) or 0)
