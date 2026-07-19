from flask import Blueprint, jsonify

from utils.datetime_utils import now_utc

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': str(now_utc())})


@health_bp.route('/')
def index():
    return jsonify({'message': 'Task Manager API', 'version': '1.0'})
