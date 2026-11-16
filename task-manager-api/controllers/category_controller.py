from flask import jsonify

from services import category_service
from utils.request_utils import get_json_body
from validators import category_validator
from views import category_view


def list_categories():
    pairs = category_service.list_with_task_counts()
    return jsonify([category_view.render_list_item(c, count) for c, count in pairs]), 200


def create_category():
    fields = category_validator.validate_create(get_json_body())
    category = category_service.create(fields)
    return jsonify(category_view.render(category)), 201


def update_category(cat_id):
    category = category_service.get(cat_id)
    fields = category_validator.validate_update(get_json_body())
    category = category_service.update(category, fields)
    return jsonify(category_view.render(category)), 200


def delete_category(cat_id):
    category_service.delete(category_service.get(cat_id))
    return jsonify({'message': 'Categoria deletada'}), 200
