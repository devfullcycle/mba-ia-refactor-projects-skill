from flask import Blueprint, request, jsonify
from controllers.category_controller import CategoryController

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    result, status = CategoryController.get_all()
    return jsonify(result), status


@category_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    result, status = CategoryController.create(data)
    return jsonify(result), status


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    result, status = CategoryController.update(cat_id, data)
    return jsonify(result), status


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    result, status = CategoryController.delete(cat_id)
    return jsonify(result), status
