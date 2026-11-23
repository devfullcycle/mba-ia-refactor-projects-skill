from flask import Blueprint, g, jsonify, request

from src.models.user_model import ROLE_ADMIN
from src.views import presenters


def build_user_routes(controller, guards):
    bp = Blueprint("users", __name__)

    @bp.get("/users")
    def list_users():
        return jsonify([presenters.user_summary(u, count) for u, count in controller.list_users()]), 200

    @bp.get("/users/<int:user_id>")
    def get_user(user_id):
        user, tasks = controller.get_user_with_tasks(user_id)
        return jsonify(presenters.user_detail(user, tasks)), 200

    @bp.post("/users")
    @guards.optional_auth  # admin required only when `role` is privileged (rule in controller)
    def create_user():
        user = controller.create_user(request.get_json(silent=True), caller=g.current_user)
        return jsonify(user.to_dict()), 201

    @bp.put("/users/<int:user_id>")
    @guards.optional_auth  # admin required only when the body changes `role`/`active`
    def update_user(user_id):
        user = controller.update_user(user_id, request.get_json(silent=True), caller=g.current_user)
        return jsonify(user.to_dict()), 200

    @bp.delete("/users/<int:user_id>")
    @guards.require_role(ROLE_ADMIN)
    def delete_user(user_id):
        controller.delete_user(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    @bp.get("/users/<int:user_id>/tasks")
    def get_user_tasks(user_id):
        return jsonify(presenters.user_task_list(controller.list_user_tasks(user_id))), 200

    @bp.post("/login")
    def login():
        user, token = controller.login(request.get_json(silent=True))
        return jsonify(presenters.login_response(user, token)), 200

    return bp
