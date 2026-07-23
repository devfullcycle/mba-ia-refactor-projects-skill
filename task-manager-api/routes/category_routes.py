from flask import Blueprint, jsonify
from controllers import category_controller

category_bp = Blueprint("categories", __name__)


def _json(result):
    body, status = result
    return jsonify(body), status


@category_bp.route("/categories", methods=["GET"])
def get_categories():
    return _json(category_controller.list_categories())


@category_bp.route("/categories", methods=["POST"])
def create_category():
    return _json(category_controller.create_category())


@category_bp.route("/categories/<int:cat_id>", methods=["PUT"])
def update_category(cat_id):
    return _json(category_controller.update_category(cat_id))


@category_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
def delete_category(cat_id):
    return _json(category_controller.delete_category(cat_id))
