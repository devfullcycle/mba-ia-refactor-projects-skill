"""Emissão e validação do token de sessão — resolve SEC-04.

O token é assinado com ``SECRET_KEY`` (mesmo segredo já usado pela aplicação)
e carrega apenas o id do usuário. O nível (`tipo`) é sempre relido do banco,
para que uma mudança de perfil tenha efeito imediato e o cliente não possa
forjar privilégios.
"""

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config import Config
from errors import NaoAutorizadoError, ProibidoError
from repositories import usuario_repository

_SALT_TOKEN = "auth-token"


def _serializer():
    if not Config.SECRET_KEY:
        raise ProibidoError("Autenticação de usuários não configurada")
    return URLSafeTimedSerializer(Config.SECRET_KEY, salt=_SALT_TOKEN)


def emitir_token(usuario):
    """Emite um token assinado para o usuário autenticado no login."""
    return _serializer().dumps({"usuario_id": usuario["id"]})


def usuario_do_token(token):
    """Valida assinatura/validade e devolve o usuário atual do banco."""
    try:
        payload = _serializer().loads(token, max_age=Config.TOKEN_MAX_AGE_SECONDS)
    except SignatureExpired:
        raise NaoAutorizadoError("Token de acesso expirado")
    except BadSignature:
        raise NaoAutorizadoError("Token de acesso inválido")

    usuario_id = payload.get("usuario_id") if isinstance(payload, dict) else None
    if not isinstance(usuario_id, int):
        raise NaoAutorizadoError("Token de acesso inválido")

    usuario = usuario_repository.buscar_por_id(usuario_id)
    if usuario is None:
        raise NaoAutorizadoError("Usuário do token não existe")
    return usuario
