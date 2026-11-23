import logging

from src.controllers import validators
from src.controllers.errors import NotFoundError
from src.models.category_model import DEFAULT_COLOR, Category

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = "Categoria não encontrada"


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
            raise NotFoundError(CATEGORY_NOT_FOUND)
        return category

    def create_category(self, data):
        data = validators.require_body(data)
        category = Category(
            name=validators.validate_name(data.get("name")),
            description=data.get("description", ""),
            color=data.get("color", DEFAULT_COLOR),
        )
        self.categories.add(category)
        self.categories.commit()
        logger.info("Categoria criada id=%s", category.id)
        return category

    def update_category(self, category_id, data):
        category = self.get_category(category_id)
        data = validators.require_body(data, allow_empty=True)
        if "name" in data:
            category.name = validators.validate_name(data["name"])
        if "description" in data:
            category.description = data["description"]
        if "color" in data:
            category.color = data["color"]
        self.categories.commit()
        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        self.tasks.clear_category(category_id)  # explicit integrity rule, same transaction
        self.categories.delete(category)
        self.categories.commit()
        logger.info("Categoria deletada id=%s", category_id)
