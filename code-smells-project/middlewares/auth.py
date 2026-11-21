"""Proteção de endpoints administrativos por token (cabeçalho X-Admin-Token)."""
import hmac
from functools import wraps

from flask import current_app, request

from middlewares.error_handler import AppError

ADMIN_TOKEN_HEADER = "X-Admin-Token"


def require_admin(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected:
            raise AppError("Endpoint administrativo desabilitado", 403)
        provided = request.headers.get(ADMIN_TOKEN_HEADER, "")
        if not hmac.compare_digest(provided.encode(), expected.encode()):
            raise AppError("Não autorizado", 401)
        return view(*args, **kwargs)

    return wrapper
