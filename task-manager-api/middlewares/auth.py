"""Autenticação por token assinado (substitui o token de fachada original).

Usa itsdangerous (dependência já trazida pelo Flask) para emitir e verificar
tokens assinados com a SECRET_KEY — sem adicionar dependências novas."""
from functools import wraps

from flask import request, g, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from middlewares.error_handler import ApiError
from models.user import User

_MAX_AGE_SECONDS = 60 * 60 * 24  # 24h


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='auth-token')


def generate_token(user):
    return _serializer().dumps({'user_id': user.id})


def _load_user_from_request():
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        raise ApiError('Token ausente ou inválido', 401)
    token = header.split(' ', 1)[1].strip()
    try:
        data = _serializer().loads(token, max_age=_MAX_AGE_SECONDS)
    except SignatureExpired:
        raise ApiError('Token expirado', 401)
    except BadSignature:
        raise ApiError('Token inválido', 401)

    user = User.get(data.get('user_id'))
    if not user:
        raise ApiError('Token inválido', 401)
    if not user.active:
        raise ApiError('Usuário inativo', 403)
    return user


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        g.current_user = _load_user_from_request()
        return view(*args, **kwargs)
    return wrapper
