from flask import Blueprint

from controllers import user_controller as c
from middlewares.auth import require_admin

user_bp = Blueprint('users', __name__)

user_bp.add_url_rule('/users', view_func=c.list_users, methods=['GET'])
user_bp.add_url_rule('/users', view_func=c.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=c.get_user, methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=c.update_user, methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_admin(c.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=c.get_user_tasks, methods=['GET'])
user_bp.add_url_rule('/login', view_func=c.login, methods=['POST'])
