"""Rotas de Categoria — blueprint próprio (no legado estavam dentro de `report_routes`)."""
from flask import Blueprint, jsonify, request


def create_category_blueprint(controller):
    blueprint = Blueprint("categories", __name__)

    @blueprint.route("/categories", methods=["GET"])
    def get_categories():
        body, status = controller.list()
        return jsonify(body), status

    @blueprint.route("/categories", methods=["POST"])
    def create_category():
        body, status = controller.create(request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/categories/<int:category_id>", methods=["PUT"])
    def update_category(category_id):
        body, status = controller.update(category_id, request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/categories/<int:category_id>", methods=["DELETE"])
    def delete_category(category_id):
        body, status = controller.delete(category_id)
        return jsonify(body), status

    return blueprint
