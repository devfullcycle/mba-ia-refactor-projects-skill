import hmac
from functools import wraps

from flask import current_app, request

from src.utils.errors import ForbiddenError, UnauthorizedError


def admin_token_required(view):
    """Protege rotas administrativas com o header X-Admin-Token (valor vindo de ADMIN_TOKEN)."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        token_esperado = current_app.config.get("ADMIN_TOKEN")
        if not token_esperado:
            raise ForbiddenError("Endpoint administrativo desabilitado")

        token_recebido = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(token_recebido, token_esperado):
            raise UnauthorizedError("Token administrativo inválido")
        return view(*args, **kwargs)

    return wrapper
