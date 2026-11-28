"""Category use cases."""
import logging

from src.controllers import validators
from src.controllers.errors import NotFoundError

logger = logging.getLogger(__name__)


class CategoryController:
    def __init__(self, categories, tasks):
        self.categories = categories
        self.tasks = tasks

    def list_categories(self):
        counts = self.tasks.count_by_category()
        return [(category, counts.get(category.id, 0)) for category in self.categories.list_all()]

    def get_category(self, category_id):
        category = self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada")
        return category

    def create_category(self, data):
        category = self.categories.new(**validators.parse_category_create(data))
        self.categories.commit()
        logger.info("Categoria criada id=%s", category.id)
        return category

    def update_category(self, category_id, data):
        category = self.get_category(category_id)
        for name, value in validators.parse_category_update(data).items():
            setattr(category, name, value)
        self.categories.commit()
        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        self.categories.delete(category)   # ORM nullifies tasks.category_id, as before
        self.categories.commit()
        logger.info("Categoria deletada id=%s", category_id)
