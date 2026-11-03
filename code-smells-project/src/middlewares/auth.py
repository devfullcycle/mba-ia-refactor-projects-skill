"""Guard para endpoints administrativos baseado em token configurado no ambiente."""
import hmac
from functools import wraps

from flask import current_app, request

from src.utils.errors import ForbiddenError, UnauthorizedError

ADMIN_TOKEN_HEADER = "X-Admin-Token"


def require_admin_token(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config.get("ADMIN_TOKEN")
        if not expected:
            raise ForbiddenError("Endpoint administrativo desabilitado (defina ADMIN_TOKEN)")
        provided = request.headers.get(ADMIN_TOKEN_HEADER, "")
        if not hmac.compare_digest(provided.encode(), expected.encode()):
            raise UnauthorizedError("Token administrativo inválido")
        return view(*args, **kwargs)

    return wrapper
