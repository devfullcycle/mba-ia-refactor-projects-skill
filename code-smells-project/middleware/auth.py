"""Guardas de autenticação e autorização — resolve SEC-04.

Duas credenciais coexistem:

- ``require_admin``: token operacional estático (``ADMIN_TOKEN``) para rotas
  de manutenção, como ``POST /admin/reset-db``. Sem a variável, falha fechado.
- ``require_tipos``: token de sessão emitido no login, assinado com
  ``SECRET_KEY`` e com validade configurável. O nível do usuário é lido da
  tabela ``usuarios`` (``admin``/``cliente``), nunca confiado ao cliente.

As rotas de cadastro de produto exigem nível ``admin``; as de cadastro de
pedido exigem nível ``cliente``.
"""

import hmac
import os
from functools import wraps

from flask import g, request

from errors import NaoAutorizadoError, ProibidoError
from services import auth_service


def _admin_token():
    return os.getenv("ADMIN_TOKEN")


def require_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        esperado = _admin_token()
        if not esperado:
            raise ProibidoError("Autenticação administrativa não configurada")

        cabecalho = request.headers.get("Authorization", "")
        prefixo = "Bearer "
        if not cabecalho.startswith(prefixo):
            raise NaoAutorizadoError("Token administrativo ausente")

        token = cabecalho[len(prefixo):]
        if not hmac.compare_digest(token, esperado):
            raise NaoAutorizadoError("Token administrativo inválido")

        return func(*args, **kwargs)

    return wrapper


def _token_do_cabecalho():
    cabecalho = request.headers.get("Authorization", "")
    prefixo = "Bearer "
    if not cabecalho.startswith(prefixo):
        raise NaoAutorizadoError("Token de acesso ausente")

    token = cabecalho[len(prefixo):].strip()
    if not token:
        raise NaoAutorizadoError("Token de acesso ausente")
    return token


def require_tipos(*tipos):
    """Exige token de sessão válido e um dos níveis de usuário informados.

    Disponibiliza o usuário autenticado em ``flask.g.usuario_atual`` para
    regras de posse (ex.: cliente só cria pedido para si mesmo).
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            usuario = auth_service.usuario_do_token(_token_do_cabecalho())
            if usuario["tipo"] not in tipos:
                raise ProibidoError("Perfil sem permissão para esta operação")

            g.usuario_atual = usuario
            return func(*args, **kwargs)

        return wrapper

    return decorator
