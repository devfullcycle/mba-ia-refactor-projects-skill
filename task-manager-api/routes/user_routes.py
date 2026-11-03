"""Rotas HTTP de Usuário e Login (camada View)."""
from flask import Blueprint, jsonify, request


def create_user_routes(controller):
    bp = Blueprint("users", __name__)

    @bp.get("/users")
    def get_users():
        return jsonify(controller.list_users()), 200

    @bp.get("/users/<int:user_id>")
    def get_user(user_id):
        return jsonify(controller.get_user(user_id)), 200

    @bp.post("/users")
    def create_user():
        return jsonify(controller.create_user(request.get_json(silent=True))), 201

    @bp.put("/users/<int:user_id>")
    def update_user(user_id):
        return jsonify(controller.update_user(user_id, request.get_json(silent=True))), 200

    @bp.delete("/users/<int:user_id>")
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    @bp.get("/users/<int:user_id>/tasks")
    def get_user_tasks(user_id):
        return jsonify(controller.user_tasks(user_id)), 200

    @bp.post("/login")
    def login():
        return jsonify(controller.login(request.get_json(silent=True))), 200

    return bp
