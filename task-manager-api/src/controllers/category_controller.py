"""Category use cases."""
import logging

from ..models.category_model import DEFAULT_COLOR, Category
from . import validators
from .errors import NotFoundError

logger = logging.getLogger(__name__)

MSG_NAME_REQUIRED = "Nome é obrigatório"


class CategoryController:
    def __init__(self, categories, tasks):
        self.categories = categories
        self.tasks = tasks

    def list_categories(self):
        return self.categories.list_with_task_counts()

    def get_category(self, category_id):
        category = self.categories.get(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada")
        return category

    def create_category(self, data):
        validators.require_payload(data)
        category = Category(
            name=validators.require_text(data.get("name"), MSG_NAME_REQUIRED),
            description=validators.optional_text(data.get("description", ""), "Descrição inválida"),
            color=validators.optional_text(data.get("color", DEFAULT_COLOR), "Cor inválida"),
        )
        self.categories.add(category)
        self.categories.commit()
        logger.info("Categoria criada id=%s", category.id)
        return category

    def update_category(self, category_id, data):
        category = self.get_category(category_id)
        validators.require_dict(data)
        if "name" in data:
            validators.require_text(data["name"], MSG_NAME_REQUIRED)
        if "description" in data:
            validators.optional_text(data["description"], "Descrição inválida")
        if "color" in data:
            validators.optional_text(data["color"], "Cor inválida")
        for field in ("name", "description", "color"):
            if field in data:
                setattr(category, field, data[field])
        self.categories.commit()
        return category

    def delete_category(self, category_id):
        category = self.get_category(category_id)
        self.tasks.detach_category(category_id)  # explicit, same transaction
        self.categories.delete(category)
        self.categories.commit()
        logger.info("Categoria deletada id=%s", category_id)
