from flask import request, jsonify
from marshmallow import ValidationError

from models.category import Category
from models.task import Task
from schemas import first_error
from schemas.category_schema import CategoryCreateSchema, CategoryUpdateSchema
from services import category_service
from middlewares.error_handler import ApiError

_create_schema = CategoryCreateSchema()
_update_schema = CategoryUpdateSchema()


def list_categories():
    result = []
    for category in Category.all():
        data = category.to_dict()
        data['task_count'] = Task.count_by_category(category.id)
        result.append(data)
    return jsonify(result), 200


def create_category():
    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)
    try:
        data = _create_schema.load(payload)
    except ValidationError as err:
        raise ApiError(first_error(err), 400)

    category = Category()
    category.name = data['name']
    category.description = data['description']
    category.color = data['color']
    category.save()
    return jsonify(category.to_dict()), 201


def update_category(cat_id):
    category = Category.get(cat_id)
    if not category:
        raise ApiError('Categoria não encontrada', 404)

    payload = request.get_json(silent=True)
    if not payload:
        raise ApiError('Dados inválidos', 400)
    try:
        data = _update_schema.load(payload)
    except ValidationError as err:
        raise ApiError(first_error(err), 400)

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    category.save()
    return jsonify(category.to_dict()), 200


def delete_category(cat_id):
    category = Category.get(cat_id)
    if not category:
        raise ApiError('Categoria não encontrada', 404)
    category_service.delete_category_safely(category)
    return jsonify({'message': 'Categoria deletada'}), 200
