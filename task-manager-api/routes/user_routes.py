from flask import Blueprint, jsonify
from controllers import user_controller

user_bp = Blueprint("users", __name__)


def _json(result):
    body, status = result
    return jsonify(body), status


@user_bp.route("/users", methods=["GET"])
def get_users():
    return _json(user_controller.list_users())


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    return _json(user_controller.get_user(user_id))


@user_bp.route("/users", methods=["POST"])
def create_user():
    return _json(user_controller.create_user())


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    return _json(user_controller.update_user(user_id))


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    return _json(user_controller.delete_user(user_id))


@user_bp.route("/users/<int:user_id>/tasks", methods=["GET"])
def get_user_tasks(user_id):
    return _json(user_controller.user_tasks(user_id))


@user_bp.route("/login", methods=["POST"])
def login():
    return _json(user_controller.login())
