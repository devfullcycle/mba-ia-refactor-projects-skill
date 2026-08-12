"""Rotas de usuários — finas, delegam à camada de serviço."""

from flask import Blueprint, request, jsonify

from services import user_service
from middlewares.error_handler import api_error_handler

user_bp = Blueprint("users", __name__)


@user_bp.route("/users", methods=["GET"])
@api_error_handler
def get_users():
    return jsonify(user_service.list_users()), 200


@user_bp.route("/users/<int:user_id>", methods=["GET"])
@api_error_handler
def get_user(user_id):
    return jsonify(user_service.get_user(user_id)), 200


@user_bp.route("/users", methods=["POST"])
@api_error_handler
def create_user():
    return jsonify(user_service.create_user(request.get_json())), 201


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
@api_error_handler
def update_user(user_id):
    return jsonify(user_service.update_user(user_id, request.get_json())), 200


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
@api_error_handler
def delete_user(user_id):
    user_service.delete_user(user_id)
    return jsonify({"message": "Usuário deletado com sucesso"}), 200


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
@api_error_handler
def get_user_tasks(user_id):
    return jsonify(user_service.get_user_tasks(user_id)), 200


@user_bp.route("/login", methods=["POST"])
@api_error_handler
def login():
    data = request.get_json() or {}
    result = user_service.login(data.get("email"), data.get("password"))
    return jsonify(result), 200