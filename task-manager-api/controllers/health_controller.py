from flask import jsonify

from utils.clock import utc_now
from utils.constants import API_VERSION


def health():
    return jsonify({'status': 'ok', 'timestamp': str(utc_now())}), 200


def index():
    return jsonify({'message': 'Task Manager API', 'version': API_VERSION}), 200
