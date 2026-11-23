from flask import Blueprint, jsonify, request

from src.views import presenters


def build_category_routes(controller):
    bp = Blueprint("categories", __name__)

    @bp.get("/categories")
    def list_categories():
        rows = controller.list_categories()
        return jsonify([presenters.category_summary(category, count) for category, count in rows]), 200

    @bp.post("/categories")
    def create_category():
        return jsonify(controller.create_category(request.get_json(silent=True)).to_dict()), 201

    @bp.put("/categories/<int:category_id>")
    def update_category(category_id):
        category = controller.update_category(category_id, request.get_json(silent=True))
        return jsonify(category.to_dict()), 200

    @bp.delete("/categories/<int:category_id>")
    def delete_category(category_id):
        controller.delete_category(category_id)
        return jsonify({"message": "Categoria deletada"}), 200

    return bp
