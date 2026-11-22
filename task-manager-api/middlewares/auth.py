"""Autenticação por token Bearer e autorização por papel (decorators de rota)."""
from functools import wraps

from flask import g, request

from services import auth_service
from utils.errors import AppError

_BEARER_PREFIX = 'Bearer '


def current_user_optional():
    """Usuário do token Bearer, ou None se ausente/inválido."""
    header = request.headers.get('Authorization', '')
    if not header.startswith(_BEARER_PREFIX):
        return None
    return auth_service.resolve_user(header[len(_BEARER_PREFIX):].strip())


def require_auth(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user_optional()
        if user is None:
            raise AppError('Autenticação necessária', 401)
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user_optional()
        if user is None:
            raise AppError('Autenticação necessária', 401)
        if not user.is_admin():
            raise AppError('Permissão de administrador necessária', 403)
        g.current_user = user
        return view(*args, **kwargs)
    return wrapper
