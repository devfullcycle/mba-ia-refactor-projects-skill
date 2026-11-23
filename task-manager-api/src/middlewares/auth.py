"""Authentication / authorization guards (AP-04). Tokens come from POST /login as `Authorization: Bearer <token>`."""
from functools import wraps

from flask import g, request

from src.controllers.errors import ForbiddenError, UnauthorizedError

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
        user = self._users.get(user_id) if user_id is not None else None
        return user if user is not None and user.active else None

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
        """401 without a valid token, 403 when the caller's role is not allowed."""
        def decorator(view):
            @wraps(view)
            def wrapper(*args, **kwargs):
                if g.current_user.role not in roles:
                    raise ForbiddenError("Acesso negado")
                return view(*args, **kwargs)
            return self.require_auth(wrapper)
        return decorator

    def optional_auth(self, view):
        """Resolves the caller (or None) for guards that depend on the request body."""
        @wraps(view)
        def wrapper(*args, **kwargs):
            g.current_user = self.current_user()
            return view(*args, **kwargs)
        return wrapper
