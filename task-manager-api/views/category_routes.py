from flask import Blueprint, request, jsonify
from controllers.category_controller import CategoryController
from middlewares.auth import login_required

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    result, status = CategoryController.get_all()
    return jsonify(result), status


@category_bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    result, status = CategoryController.create(request.get_json() or {})
    return jsonify(result), status


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@login_required
def update_category(cat_id):
    result, status = CategoryController.update(cat_id, request.get_json())
    return jsonify(result), status


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@login_required
def delete_category(cat_id):
    result, status = CategoryController.delete(cat_id)
    return jsonify(result), status
