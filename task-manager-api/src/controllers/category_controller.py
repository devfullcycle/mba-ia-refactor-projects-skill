"""Controller de Categoria — extraído de `report_routes.py`, onde o CRUD estava misturado
aos relatórios."""
import logging

from src.extensions import db
from src.middlewares.error_handler import NotFoundError
from src.models.category import Category
from src.validators.category_validator import validate_category

logger = logging.getLogger(__name__)


class CategoryController:
    def list(self):
        return [
            {**categoria.to_dict(), "task_count": total}
            for categoria, total in Category.list_with_task_counts()
        ], 200

    def create(self, dados):
        campos = validate_category(dados)
        categoria = Category(**campos)
        db.session.add(categoria)
        db.session.commit()
        logger.info("Categoria criada", extra={"category_id": categoria.id})
        return categoria.to_dict(), 201

    def update(self, category_id, dados):
        categoria = self._get_or_fail(category_id)
        campos = validate_category(dados, partial=True)
        for campo, valor in campos.items():
            setattr(categoria, campo, valor)
        db.session.commit()
        logger.info("Categoria atualizada", extra={"category_id": category_id})
        return categoria.to_dict(), 200

    def delete(self, category_id):
        categoria = self._get_or_fail(category_id)
        db.session.delete(categoria)
        db.session.commit()
        logger.info("Categoria removida", extra={"category_id": category_id})
        return {"message": "Categoria deletada"}, 200

    @staticmethod
    def _get_or_fail(category_id):
        categoria = Category.get(category_id)
        if categoria is None:
            raise NotFoundError("Categoria não encontrada")
        return categoria
