from flask import Blueprint, jsonify, request

from controllers import category_controller
from middlewares.auth import require_auth

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route('/categories', methods=['POST'])
def create_category():
    return jsonify(category_controller.create_category(request.get_json())), 201


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    return jsonify(category_controller.update_category(cat_id, request.get_json())), 200


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@require_auth
def delete_category(cat_id):
    return jsonify(category_controller.delete_category(cat_id)), 200
