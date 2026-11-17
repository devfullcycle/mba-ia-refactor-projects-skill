from flask import Blueprint, request, jsonify
from controllers.user_controller import UserController

user_bp = Blueprint('users', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    response, status_code = UserController.get_all_users()
    return jsonify(response), status_code

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    response, status_code = UserController.get_user_by_id(user_id)
    return jsonify(response), status_code

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    response, status_code = UserController.create_user(data)
    return jsonify(response), status_code

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    response, status_code = UserController.update_user(user_id, data)
    return jsonify(response), status_code

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    response, status_code = UserController.delete_user(user_id)
    return jsonify(response), status_code

@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    response, status_code = UserController.get_user_tasks(user_id)
    return jsonify(response), status_code

@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    response, status_code = UserController.login(data)
    return jsonify(response), status_code
