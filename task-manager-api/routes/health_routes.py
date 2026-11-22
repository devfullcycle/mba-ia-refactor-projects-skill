from flask import Blueprint

from utils.helpers import utc_now

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(utc_now())}


@health_bp.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}
