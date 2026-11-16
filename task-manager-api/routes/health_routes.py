from flask import Blueprint

from controllers import health_controller as c

health_bp = Blueprint('health', __name__)

health_bp.add_url_rule('/health', view_func=c.health, methods=['GET'])
health_bp.add_url_rule('/', view_func=c.index, methods=['GET'])
