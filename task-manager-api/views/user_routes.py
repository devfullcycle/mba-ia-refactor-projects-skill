from flask import Blueprint, request, jsonify
from controllers.user_controller import UserController
from middlewares.auth import login_required

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    result, status = UserController.get_all()
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    result, status = UserController.get_by_id(user_id)
    return jsonify(result), status


@user_bp.route('/users', methods=['POST'])
def create_user():
    result, status = UserController.create(request.get_json() or {})
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    result, status = UserController.update(user_id, request.get_json() or {})
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    result, status = UserController.delete(user_id)
    return jsonify(result), status


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    result, status = UserController.get_tasks(user_id)
    return jsonify(result), status


@user_bp.route('/login', methods=['POST'])
def login():
    result, status = UserController.login(request.get_json() or {})
    return jsonify(result), status
