from flask import Blueprint

from controllers import user_controller as user_ctrl
from middlewares.auth import require_admin, require_auth

user_bp = Blueprint('users', __name__)

# Dados de usuários (e-mail, role) só para autenticados. POST /users e /login são
# públicos por design (registro e login); o registro não concede role privilegiado.
user_bp.add_url_rule('/users', view_func=require_auth(user_ctrl.list_users), methods=['GET'])
user_bp.add_url_rule('/users', view_func=user_ctrl.create_user, methods=['POST'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_auth(user_ctrl.get_user), methods=['GET'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_auth(user_ctrl.update_user), methods=['PUT'])
user_bp.add_url_rule('/users/<int:user_id>', view_func=require_admin(user_ctrl.delete_user), methods=['DELETE'])
user_bp.add_url_rule('/users/<int:user_id>/tasks', view_func=require_auth(user_ctrl.get_user_tasks),
                     methods=['GET'])
user_bp.add_url_rule('/login', view_func=user_ctrl.login, methods=['POST'])
