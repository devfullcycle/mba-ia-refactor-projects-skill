"""Emissão e verificação de tokens de acesso assinados com SECRET_KEY (itsdangerous, dependência do Flask)."""
from flask import current_app
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SALT_TOKEN = "auth-token"


class TokenInvalidoError(Exception):
    pass


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=SALT_TOKEN)


def gerar_token(usuario_id):
    return _serializer().dumps({"uid": usuario_id})


def ler_usuario_id(token):
    try:
        payload = _serializer().loads(token, max_age=current_app.config["TOKEN_TTL_SEGUNDOS"])
    except SignatureExpired as exc:
        raise TokenInvalidoError("Token expirado") from exc
    except BadSignature as exc:
        raise TokenInvalidoError("Token inválido") from exc
    return payload.get("uid")
