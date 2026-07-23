"""Views HTTP de usuários e login."""

from flask import Blueprint, jsonify, request

from routes.auth import ADMIN_ROLES, require_roles
from routes.dependencies import get_controller
from schemas.presenters import (
    present_login,
    present_message,
    present_user,
    present_user_detail,
    present_user_list_item,
    present_user_tasks,
)


user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
@require_roles(*ADMIN_ROLES)
def get_users():
    users = get_controller("users").list()
    return jsonify(
        [present_user_list_item(user, task_count=count) for user, count in users]
    ), 200


@user_bp.route("/users/<int:user_id>", methods=["GET"])
@require_roles(*ADMIN_ROLES)
def get_user(user_id):
    return jsonify(present_user_detail(get_controller("users").get(user_id))), 200


@user_bp.route("/users", methods=["POST"])
@require_roles(*ADMIN_ROLES)
def create_user():
    user = get_controller("users").create(request.get_json(silent=True))
    return jsonify(present_user(user)), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
@require_roles(*ADMIN_ROLES)
def update_user(user_id):
    user = get_controller("users").update(
        user_id,
        request.get_json(silent=True),
    )
    return jsonify(present_user(user)), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@require_roles(*ADMIN_ROLES)
def delete_user(user_id):
    get_controller("users").delete(user_id)
    return jsonify(present_message("Usuário deletado com sucesso")), 200


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
@require_roles(*ADMIN_ROLES)
def get_user_tasks(user_id):
    tasks = get_controller("users").list_tasks(user_id)
    return jsonify(present_user_tasks(tasks)), 200


@user_bp.route("/login", methods=["POST"])
def login():
    user, token = get_controller("users").login(request.get_json(silent=True))
    return jsonify(present_login(user, token)), 200
