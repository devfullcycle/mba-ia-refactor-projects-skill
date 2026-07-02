from functools import wraps

from flask import g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import settings

_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt='auth-token')


def generate_token(user_id):
    return _serializer.dumps({'user_id': user_id})


def decode_token(token):
    try:
        data = _serializer.loads(token, max_age=settings.TOKEN_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    return data.get('user_id')


def token_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autenticação ausente'}), 401

        token = auth_header[len('Bearer '):]
        user_id = decode_token(token)
        if user_id is None:
            return jsonify({'error': 'Token inválido ou expirado'}), 401

        g.user_id = user_id
        return view(*args, **kwargs)

    return wrapper
