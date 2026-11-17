from datetime import datetime

from flask import jsonify


def health():
    return jsonify({'status': 'ok', 'timestamp': str(datetime.now())}), 200


def index():
    return jsonify({'message': 'Task Manager API', 'version': '1.0'}), 200
