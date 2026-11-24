"""Autenticação por token assinado (itsdangerous) enviado em `Authorization: Bearer <token>`.

Os decorators daqui só dizem *quem* pode chamar a rota (autenticado / staff / admin).
Regras que dependem do recurso (dono da task, campos privilegiados) ficam em
`services/access_policy.py` e são aplicadas pelo controller antes de persistir.
"""
import hmac
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
    # 'pv' amarra o token à senha atual: trocar a senha invalida tokens já emitidos.
    return _serializer().dumps({'id': user.id, 'role': user.role, 'pv': user.credential_fingerprint()})


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
    if not hmac.compare_digest(str(payload.get('pv', '')), user.credential_fingerprint()):
        raise AuthenticationError('Token inválido ou expirado')
    g.current_user = user
    return user


def current_user():
    """Usuário autenticado no request atual (a rota deve estar protegida)."""
    return g.current_user


def require_admin_user():
    user = authenticate_request()
    if not user.is_admin():
        raise ForbiddenError('Acesso restrito a administradores')
    return user


def require_staff_user():
    user = authenticate_request()
    if not user.is_staff():
        raise ForbiddenError('Acesso restrito a administradores e gerentes')
    return user


def _guard(check):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            check()
            return view(*args, **kwargs)
        return wrapper
    return decorator


require_auth = _guard(authenticate_request)
require_staff = _guard(require_staff_user)
require_admin = _guard(require_admin_user)
