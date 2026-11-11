from flask import Blueprint, jsonify, request

from src.controllers import category_controller
from src.middlewares.auth import login_required, staff_required

category_bp = Blueprint("categories", __name__)


@category_bp.route("/categories", methods=["GET"])
@login_required
def get_categories():
    return jsonify(category_controller.list_categories()), 200


@category_bp.route("/categories", methods=["POST"])
@staff_required
def create_category():
    return jsonify(category_controller.create_category(request.get_json(silent=True))), 201


@category_bp.route("/categories/<int:category_id>", methods=["PUT"])
@staff_required
def update_category(category_id):
    return jsonify(category_controller.update_category(category_id, request.get_json(silent=True))), 200


@category_bp.route("/categories/<int:category_id>", methods=["DELETE"])
@staff_required
def delete_category(category_id):
    return jsonify(category_controller.delete_category(category_id)), 200
