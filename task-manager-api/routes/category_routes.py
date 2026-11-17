from flask import Blueprint

from controllers import category_controller as c
from middlewares.auth import require_auth

category_bp = Blueprint('categories', __name__)

category_bp.add_url_rule('/categories', view_func=c.list_categories, methods=['GET'])
category_bp.add_url_rule('/categories', view_func=c.create_category, methods=['POST'])
category_bp.add_url_rule('/categories/<int:cat_id>', view_func=c.update_category, methods=['PUT'])
category_bp.add_url_rule('/categories/<int:cat_id>', view_func=require_auth(c.delete_category), methods=['DELETE'])
