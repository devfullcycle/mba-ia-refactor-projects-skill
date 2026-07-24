"""Rotas de Usuário e autenticação.

Alteração e remoção de conta exigem token (o próprio usuário ou um admin) — no legado,
qualquer cliente podia alterar ou apagar qualquer conta.
"""
from flask import Blueprint, jsonify, request


def create_user_blueprint(controller, auth):
    blueprint = Blueprint("users", __name__)
    require_self_or_admin = auth["require_self_or_admin"]

    @blueprint.route("/users", methods=["GET"])
    def get_users():
        body, status = controller.list()
        return jsonify(body), status

    @blueprint.route("/users/<int:user_id>", methods=["GET"])
    def get_user(user_id):
        body, status = controller.get(user_id)
        return jsonify(body), status

    @blueprint.route("/users", methods=["POST"])
    def create_user():
        body, status = controller.create(request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/users/<int:user_id>", methods=["PUT"])
    @require_self_or_admin
    def update_user(user_id):
        body, status = controller.update(user_id, request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/users/<int:user_id>", methods=["DELETE"])
    @require_self_or_admin
    def delete_user(user_id):
        body, status = controller.delete(user_id)
        return jsonify(body), status

    @blueprint.route("/users/<int:user_id>/tasks", methods=["GET"])
    def get_user_tasks(user_id):
        body, status = controller.tasks(user_id)
        return jsonify(body), status

    @blueprint.route("/login", methods=["POST"])
    def login():
        body, status = controller.login(request.get_json(silent=True))
        return jsonify(body), status

    return blueprint
