from flask import Blueprint

from controllers import user_controller, auth_controller
from middlewares.auth import require_auth

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/users', 'list_users', user_controller.list_users, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', 'get_user', user_controller.get_user, methods=['GET'])
user_bp.add_url_rule('/users', 'create_user', user_controller.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', 'update_user', user_controller.update_user, methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', 'delete_user',
                    require_auth(user_controller.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', 'get_user_tasks',
                    user_controller.get_user_tasks, methods=['GET'])
user_bp.add_url_rule('/login', 'login', auth_controller.login, methods=['POST'])
