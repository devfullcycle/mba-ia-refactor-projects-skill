"""Rotas HTTP de Categoria (camada View) — antes misturadas em report_routes.py."""
from flask import Blueprint, jsonify, request


def create_category_routes(controller):
    bp = Blueprint("categories", __name__)

    @bp.get("/categories")
    def get_categories():
        return jsonify(controller.list_categories()), 200

    @bp.post("/categories")
    def create_category():
        return jsonify(controller.create_category(request.get_json(silent=True))), 201

    @bp.put("/categories/<int:cat_id>")
    def update_category(cat_id):
        return jsonify(controller.update_category(cat_id, request.get_json(silent=True))), 200

    @bp.delete("/categories/<int:cat_id>")
    def delete_category(cat_id):
        controller.delete_category(cat_id)
        return jsonify({"message": "Categoria deletada"}), 200

    return bp
