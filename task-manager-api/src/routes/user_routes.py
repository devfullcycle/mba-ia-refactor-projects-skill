from flask import Blueprint, jsonify, request

from src.controllers import user_controller
from src.middlewares.auth import admin_required, current_user, login_required, optional_auth
from src.utils.pagination import pagination_headers, parse_page

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    page = parse_page(request.args)
    users, total = user_controller.list_users(page)
    return jsonify(users), 200, pagination_headers(total, page)


@user_bp.route("/users/<int:user_id>", methods=["GET"])
@login_required
def get_user(user_id):
    return jsonify(user_controller.get_user(user_id)), 200


@user_bp.route("/users", methods=["POST"])
def create_user():
    # Cadastro público; o token (se enviado) só é usado para um admin escolher o role.
    actor = optional_auth()
    return jsonify(user_controller.create_user(request.get_json(silent=True), actor)), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
@login_required
def update_user(user_id):
    return jsonify(user_controller.update_user(user_id, request.get_json(silent=True), current_user())), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    return jsonify(user_controller.delete_user(user_id, current_user())), 200


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
@login_required
def get_user_tasks(user_id):
    return jsonify(user_controller.get_user_tasks(user_id)), 200
