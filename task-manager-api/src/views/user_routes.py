"""User and login endpoints (HTTP layer only)."""
from flask import Blueprint, g, jsonify, request

from src.views.presenters import present_user, present_user_detail, present_user_summary, present_user_task


def build_user_routes(controller, guards):
    bp = Blueprint("users", __name__)

    @bp.get("/users")
    def list_users():
        return jsonify([present_user_summary(user, count) for user, count in controller.list_users()]), 200

    @bp.get("/users/<int:user_id>")
    def get_user(user_id):
        user, tasks = controller.get_user_with_tasks(user_id)
        return jsonify(present_user_detail(user, tasks)), 200

    @bp.post("/users")
    @guards.optional_auth  # admin required only when a privileged role is requested
    def create_user():
        user = controller.create_user(request.get_json(silent=True), caller=g.current_user)
        return jsonify(present_user(user)), 201

    @bp.put("/users/<int:user_id>")
    @guards.optional_auth  # role/active: admin; password/email: owner or admin
    def update_user(user_id):
        user = controller.update_user(user_id, request.get_json(silent=True), caller=g.current_user)
        return jsonify(present_user(user)), 200

    @bp.delete("/users/<int:user_id>")
    @guards.require_admin
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    @bp.get("/users/<int:user_id>/tasks")
    def get_user_tasks(user_id):
        return jsonify([present_user_task(task) for task in controller.list_user_tasks(user_id)]), 200

    @bp.post("/login")
    def login():
        user, token = controller.login(request.get_json(silent=True))
        return jsonify({"message": "Login realizado com sucesso", "user": present_user(user), "token": token}), 200

    return bp
