"""Guarda de endpoints administrativos via cabeçalho X-Admin-Token (desativados se ADMIN_TOKEN não estiver definido)."""
import hmac
from functools import wraps

from flask import request

from ..controllers.errors import ForbiddenError


def build_require_admin(admin_token: str):
    def require_admin(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            enviado = request.headers.get("X-Admin-Token", "")
            if not admin_token or not hmac.compare_digest(enviado.encode(), admin_token.encode()):
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return wrapper

    return require_admin
