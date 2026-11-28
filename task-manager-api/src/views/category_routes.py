"""Category endpoints (HTTP layer only)."""
from flask import Blueprint, jsonify, request

from src.views.presenters import present_category


def build_category_routes(controller):
    bp = Blueprint("categories", __name__)

    @bp.get("/categories")
    def list_categories():
        return jsonify([present_category(cat, count) for cat, count in controller.list_categories()]), 200

    @bp.post("/categories")
    def create_category():
        return jsonify(present_category(controller.create_category(request.get_json(silent=True)))), 201

    @bp.put("/categories/<int:cat_id>")
    def update_category(cat_id):
        category = controller.update_category(cat_id, request.get_json(silent=True))
        return jsonify(present_category(category)), 200

    @bp.delete("/categories/<int:cat_id>")
    def delete_category(cat_id):
        controller.delete_category(cat_id)
        return jsonify({"message": "Categoria deletada"}), 200

    return bp
