"""Autenticação e autorização na fronteira HTTP."""

from functools import wraps

from flask import g, request

from errors import ForbiddenError, UnauthorizedError
from routes.dependencies import get_controller


ALL_ROLES = ("user", "manager", "admin")
MANAGEMENT_ROLES = ("manager", "admin")
ADMIN_ROLES = ("admin",)


def require_roles(*allowed_roles):
    """Exige Bearer token válido e, quando informado, um dos papéis permitidos."""

    allowed = frozenset(allowed_roles)

    def decorate(handler):
        @wraps(handler)
        def authenticated(*args, **kwargs):
            authorization = request.headers.get("Authorization", "")
            scheme, separator, token = authorization.partition(" ")
            if (
                not separator
                or scheme.lower() != "bearer"
                or not token.strip()
                or " " in token.strip()
            ):
                raise UnauthorizedError("Autenticação obrigatória")

            user = get_controller("users").authenticate_token(token.strip())
            if allowed and user.role not in allowed:
                raise ForbiddenError("Permissão insuficiente")
            g.current_user = user
            return handler(*args, **kwargs)

        return authenticated

    return decorate
