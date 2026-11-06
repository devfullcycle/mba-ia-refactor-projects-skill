"""Middleware de autenticação e autorização JWT (default deny).

A proteção é fail-closed: toda rota de escrita exige `Authorization: Bearer <token>`
por padrão, sem depender de flag opt-in. Rotas administrativas usam o decorator
`require_role('admin')`; identidade, papel e posse nunca são lidos do body.
"""

from functools import wraps

import jwt
from flask import g, request

from database import db
from errors import ForbiddenError, UnauthorizedError
from models.user import User
from services.auth_service import decode_access_token

SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}
EXEMPT_PATHS = {'/login'}


def authenticate_request():
    """Autentica o request atual e popula `g.current_user`, `g.user_id` e `g.user_role`.

    Idempotente por request. O usuário é carregado a partir do `sub` do JWT,
    garantindo que tokens de usuários removidos/inativos deixem de valer. O papel
    é lido do cadastro autenticado, nunca de `role` enviado pelo cliente.
    """
    current_request = request._get_current_object()
    if (getattr(g, 'current_user', None) is not None
            and getattr(g, '_auth_request', None) is current_request):
        return g.current_user

    header = request.headers.get('Authorization', '')
    if not header.startswith('Bearer '):
        raise UnauthorizedError('Autenticação necessária')

    token = header[len('Bearer '):].strip()
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise UnauthorizedError('Token inválido ou expirado')

    try:
        user_id = int(payload.get('sub'))
    except (TypeError, ValueError):
        raise UnauthorizedError('Token inválido')

    user = db.session.get(User, user_id)
    if user is None or not user.active:
        raise UnauthorizedError('Usuário não encontrado ou inativo')

    g.current_user = user
    g.user_id = user.id
    g.user_role = user.role
    g._auth_request = current_request
    return user


def require_auth(view):
    """Garante autenticação mesmo em rotas que não passam pelo guard global."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        authenticate_request()
        return view(*args, **kwargs)

    return wrapped


def require_role(*roles):
    """Restringe a rota aos papéis informados (ex.: `@require_role('admin')`)."""

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            authenticate_request()
            if g.user_role not in roles:
                raise ForbiddenError('Acesso restrito')
            return view(*args, **kwargs)

        return wrapped

    return decorator


def init_auth(app):
    @app.before_request
    def enforce_authentication():
        # `/login` é público; métodos de leitura preservam o contrato original.
        if request.method in SAFE_METHODS or request.path in EXEMPT_PATHS:
            return None

        # Fail-closed: a autenticação não é desativada por configuração.
        authenticate_request()
        return None
