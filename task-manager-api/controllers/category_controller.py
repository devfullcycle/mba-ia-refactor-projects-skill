"""Casos de uso de categorias."""
import logging

from config.constants import DEFAULT_COLOR
from controllers.common import get_or_404, persistence_errors
from models.category import Category
from models.task import Task
from utils import validators
from utils.errors import AppError

logger = logging.getLogger(__name__)

CATEGORY_NOT_FOUND = 'Categoria não encontrada'


def _validate_name(value):
    if not value or not isinstance(value, str):
        raise AppError('Nome é obrigatório', 400)
    return value


def list_categories():
    counts = Task.totals_by_category()
    result = []
    for category in Category.list_all():
        data = category.to_dict()
        data['task_count'] = counts.get(category.id, 0)
        result.append(data)
    return result


def create_category(data):
    validators.require_json_object(data)
    name = _validate_name(data.get('name'))

    category = Category(
        name=name,
        description=data.get('description', ''),
        color=validators.validate_color(data.get('color', DEFAULT_COLOR)),
    )
    with persistence_errors('Erro ao criar categoria'):
        category.save()
    return category.to_dict()


def update_category(category_id, data):
    category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
    validators.require_json_object(data, allow_empty=True)

    if 'name' in data:
        category.name = _validate_name(data['name'])
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = validators.validate_color(data['color'])

    with persistence_errors('Erro ao atualizar'):
        category.save()
    return category.to_dict()


def delete_category(category_id):
    category = get_or_404(Category, category_id, CATEGORY_NOT_FOUND)
    with persistence_errors('Erro ao deletar'):
        category.delete()
    return {'message': 'Categoria deletada'}
