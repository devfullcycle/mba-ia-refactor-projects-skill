"""Autenticação por token assinado (itsdangerous) enviado em `Authorization: Bearer <token>`."""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, URLSafeTimedSerializer

from database import db
from models.user import User
from utils.errors import AuthenticationError, ForbiddenError

_SALT = 'task-manager-auth'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)


def issue_token(user):
    return _serializer().dumps({'id': user.id, 'role': user.role})


def authenticate_request():
    """Valida o token do request e devolve o usuário (ou levanta 401)."""
    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        raise AuthenticationError('Autenticação necessária')
    try:
        payload = _serializer().loads(
            header[len('Bearer '):].strip(), max_age=current_app.config['TOKEN_MAX_AGE'])
    except BadSignature:  # inclui SignatureExpired
        raise AuthenticationError('Token inválido ou expirado')
    user = db.session.get(User, payload.get('id'))
    if not user or not user.active:
        raise AuthenticationError('Token inválido ou expirado')
    g.current_user = user
    return user


def require_admin_user():
    user = authenticate_request()
    if not user.is_admin():
        raise ForbiddenError('Acesso restrito a administradores')
    return user


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        authenticate_request()
        return view(*args, **kwargs)
    return wrapper


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        require_admin_user()
        return view(*args, **kwargs)
    return wrapper
