from flask import Blueprint

from controllers import category_controller as category_ctrl
from middlewares.auth import require_admin

category_bp = Blueprint('categories', __name__)

# Categorias são compartilhadas por todos: leitura pública, mutação só por admin.
category_bp.add_url_rule('/categories', view_func=category_ctrl.list_categories, methods=['GET'])
category_bp.add_url_rule('/categories', view_func=require_admin(category_ctrl.create_category), methods=['POST'])
category_bp.add_url_rule('/categories/<int:cat_id>', view_func=require_admin(category_ctrl.update_category),
                         methods=['PUT'])
category_bp.add_url_rule('/categories/<int:cat_id>', view_func=require_admin(category_ctrl.delete_category),
                         methods=['DELETE'])
