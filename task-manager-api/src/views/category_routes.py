"""HTTP layer for categories."""
from flask import Blueprint, jsonify, request

from .presenters import present_category_with_count


def build_category_blueprint(controller):
    bp = Blueprint("categories", __name__)

    @bp.get("/categories")
    def list_categories():
        rows = controller.list_categories()
        return jsonify([present_category_with_count(c, n) for c, n in rows]), 200

    @bp.post("/categories")
    def create_category():
        category = controller.create_category(request.get_json(silent=True))
        return jsonify(category.to_dict()), 201

    @bp.put("/categories/<int:cat_id>")
    def update_category(cat_id):
        category = controller.update_category(cat_id, request.get_json(silent=True))
        return jsonify(category.to_dict()), 200

    @bp.delete("/categories/<int:cat_id>")
    def delete_category(cat_id):
        controller.delete_category(cat_id)
        return jsonify({"message": "Categoria deletada"}), 200

    return bp
