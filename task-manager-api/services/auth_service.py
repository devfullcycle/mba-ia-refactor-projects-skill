"""Emissão e verificação de tokens de acesso assinados (itsdangerous, já dependência do Flask)."""
from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

from models.user import User

_SALT = 'task-manager-auth'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_SALT)


def issue_token(user):
    return _serializer().dumps({'uid': user.id})


def resolve_user(token):
    """Devolve o usuário ativo dono do token, ou None se inválido/expirado."""
    if not token:
        return None
    try:
        payload = _serializer().loads(token, max_age=current_app.config['TOKEN_MAX_AGE_SECONDS'])
    except BadSignature:  # inclui SignatureExpired
        return None
    user = User.find(payload.get('uid')) if isinstance(payload, dict) else None
    if user is None or not user.active:
        return None
    return user
