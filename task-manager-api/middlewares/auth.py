from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({'error': 'Token de autenticação inválido ou ausente'}), 401
        return f(*args, **kwargs)
    return decorated


def get_current_user_id():
    return int(get_jwt_identity())
