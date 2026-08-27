from flask import Blueprint
import controllers.user_controller as user_controller

user_bp = Blueprint('users', __name__)

user_bp.route('/users', methods=['GET'])(user_controller.get_users)
user_bp.route('/users/<int:user_id>', methods=['GET'])(user_controller.get_user)
user_bp.route('/users', methods=['POST'])(user_controller.create_user)
user_bp.route('/users/<int:user_id>', methods=['PUT'])(user_controller.update_user)
user_bp.route('/users/<int:user_id>', methods=['DELETE'])(user_controller.delete_user)
user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])(user_controller.get_user_tasks)
user_bp.route('/login', methods=['POST'])(user_controller.login)
