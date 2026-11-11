"""Emissão e verificação de tokens assinados com SECRET_KEY (itsdangerous, dependência do Flask)."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

TOKEN_SALT = "auth-token"


class InvalidTokenError(Exception):
    pass


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=TOKEN_SALT)


def generate_token(user_id):
    return _serializer().dumps({"uid": user_id})


def read_user_id(token):
    try:
        payload = _serializer().loads(token, max_age=current_app.config["TOKEN_TTL_SECONDS"])
    except SignatureExpired as exc:
        raise InvalidTokenError("Token expirado") from exc
    except BadSignature as exc:
        raise InvalidTokenError("Token inválido") from exc
    return payload.get("uid")
