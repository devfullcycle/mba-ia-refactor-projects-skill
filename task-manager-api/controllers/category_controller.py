"""Fluxo dos casos de uso de Categoria."""
from models.category import Category
from models.task import Task
from utils.errors import NotFoundError
from validators.category_validator import validate_category_update, validate_new_category


class CategoryController:
    def __init__(self, session):
        self._session = session

    @staticmethod
    def _get_or_404(category_id):
        category = Category.get(category_id)
        if not category:
            raise NotFoundError("Categoria não encontrada")
        return category

    def list_categories(self):
        counts = Task.count_by(Task.category_id)
        return [{**c.to_dict(), "task_count": counts.get(c.id, 0)} for c in Category.all()]

    def create_category(self, data):
        category = Category(**validate_new_category(data))
        self._session.add(category)
        self._session.commit()
        return category.to_dict()

    def update_category(self, category_id, data):
        category = self._get_or_404(category_id)
        for key, value in validate_category_update(data).items():
            setattr(category, key, value)
        self._session.commit()
        return category.to_dict()

    def delete_category(self, category_id):
        category = self._get_or_404(category_id)
        Task.detach_category(category_id)  # evita tasks apontando para categoria inexistente
        self._session.delete(category)
        self._session.commit()
