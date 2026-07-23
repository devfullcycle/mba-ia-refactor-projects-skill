from __future__ import annotations

from errors import NotFoundError
from models.category import Category
from schemas.validators import validate_category_create, validate_category_update

from controllers.base import validate


class CategoryController:
    def __init__(self, categories, session):
        self.categories = categories
        self.session = session

    def list(self):
        return self.categories.list_with_task_counts()

    def create(self, payload):
        data = validate(validate_category_create, payload)
        category = Category(**data)
        self.categories.add(category)
        self.session.commit()
        return category

    def update(self, category_id, payload):
        category = self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada")
        data = validate(validate_category_update, payload)
        for field, value in data.items():
            setattr(category, field, value)
        self.session.commit()
        return category

    def delete(self, category_id):
        category = self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada")
        self.categories.delete_and_detach_tasks(category)
        self.session.commit()
