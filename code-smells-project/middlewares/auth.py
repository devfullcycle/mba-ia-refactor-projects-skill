import hmac
from functools import wraps

from flask import request

from config import settings
from exceptions import ForbiddenError, UnauthorizedError


def admin_required(view):
    """Exige o header X-Admin-Token igual a ADMIN_TOKEN. Sem token configurado, desabilita a rota."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not settings.ADMIN_TOKEN:
            raise ForbiddenError("Rotas administrativas desabilitadas (ADMIN_TOKEN não configurado)")
        enviado = request.headers.get("X-Admin-Token", "")
        if not hmac.compare_digest(enviado, settings.ADMIN_TOKEN):
            raise UnauthorizedError("Token administrativo inválido")
        return view(*args, **kwargs)

    return wrapper
