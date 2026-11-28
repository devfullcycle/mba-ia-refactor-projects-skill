"""Authentication / authorization guards (Bearer token issued by POST /login)."""
from functools import wraps

from flask import g, request

from src.controllers.errors import ForbiddenError, UnauthorizedError
from src.models.constants import ROLE_ADMIN

BEARER_PREFIX = "Bearer "


class Guards:
    def __init__(self, tokens, users):
        self._tokens = tokens
        self._users = users

    def current_user(self):
        header = request.headers.get("Authorization", "")
        if not header.startswith(BEARER_PREFIX):
            return None
        user_id = self._tokens.verify(header[len(BEARER_PREFIX):])
        user = self._users.get(user_id) if isinstance(user_id, int) else None
        return user if user is not None and user.active else None

    def optional_auth(self, view):
        """Resolves the caller (or None) for conditional guards evaluated in controllers."""
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = self.current_user()
            return view(*args, **kwargs)
        return wrapper

    def require_auth(self, view):
        """401 when there is no valid token."""
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = self.current_user()
            if g.current_user is None:
                raise UnauthorizedError("Autenticação necessária")
            return view(*args, **kwargs)
        return wrapper

    def require_role(self, *roles):
        """403 when authenticated but the role is not allowed."""
        def decorator(view):
            @wraps(view)
            def checked(*args, **kwargs):
                if g.current_user.role not in roles:
                    raise ForbiddenError("Acesso negado")
                return view(*args, **kwargs)
            return self.require_auth(checked)
        return decorator

    def require_admin(self, view):
        return self.require_role(ROLE_ADMIN)(view)
