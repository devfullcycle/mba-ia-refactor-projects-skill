from flask import Blueprint

from controllers import health_controller as health_ctrl

health_bp = Blueprint('health', __name__)

health_bp.add_url_rule('/health', view_func=health_ctrl.health, methods=['GET'])
health_bp.add_url_rule('/', view_func=health_ctrl.index, methods=['GET'])
