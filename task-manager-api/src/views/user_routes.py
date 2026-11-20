"""HTTP layer for users and login."""
from flask import Blueprint, jsonify, request

from ..middlewares.auth import authenticated_user_id
from .presenters import present_user_task, present_user_with_count


def build_user_blueprint(controller, token_service):
    bp = Blueprint("users", __name__)

    @bp.get("/users")
    def list_users():
        return jsonify([present_user_with_count(u, n) for u, n in controller.list_users()]), 200

    @bp.get("/users/<int:user_id>")
    def get_user(user_id):
        user, tasks = controller.get_user_with_tasks(user_id)
        data = user.to_dict()
        data["tasks"] = [t.to_dict() for t in tasks]
        return jsonify(data), 200

    @bp.post("/users")
    def create_user():
        actor_id = authenticated_user_id(token_service)
        user = controller.create_user(request.get_json(silent=True), actor_id)
        return jsonify(user.to_dict()), 201

    @bp.put("/users/<int:user_id>")
    def update_user(user_id):
        actor_id = authenticated_user_id(token_service)
        user = controller.update_user(user_id, request.get_json(silent=True), actor_id)
        return jsonify(user.to_dict()), 200

    @bp.delete("/users/<int:user_id>")
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    @bp.get("/users/<int:user_id>/tasks")
    def get_user_tasks(user_id):
        return jsonify([present_user_task(t) for t in controller.list_user_tasks(user_id)]), 200

    @bp.post("/login")
    def login():
        user, token = controller.login(request.get_json(silent=True))
        return jsonify({"message": "Login realizado com sucesso", "user": user.to_dict(), "token": token}), 200

    return bp
