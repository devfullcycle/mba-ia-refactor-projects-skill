from flask import Blueprint

from controllers import category_controller
from middlewares.auth import require_auth

category_bp = Blueprint('categories', __name__)

category_bp.add_url_rule('/categories', 'list_categories',
                        category_controller.list_categories, methods=['GET'])
category_bp.add_url_rule('/categories', 'create_category',
                        category_controller.create_category, methods=['POST'])
category_bp.add_url_rule('/categories/<int:cat_id>', 'update_category',
                        category_controller.update_category, methods=['PUT'])
category_bp.add_url_rule('/categories/<int:cat_id>', 'delete_category',
                        require_auth(category_controller.delete_category), methods=['DELETE'])
