"""Autenticação e autorização.

O legado não tinha nenhuma verificação: qualquer cliente lia os relatórios de todos os
usuários e apagava contas. As rotas protegidas negam por default — sem token válido, 401.
"""
import logging
from functools import wraps

from flask import g, request

from src.domain.constants import ROLE_ADMIN
from src.middlewares.error_handler import ForbiddenError, UnauthorizedError

logger = logging.getLogger(__name__)

BEARER_PREFIX = "Bearer "


def create_auth_middleware(token_service, user_loader):
    """Devolve os decoradores de autenticação, com as dependências já injetadas."""

    def _authenticate():
        header = request.headers.get("Authorization", "")
        if not header.startswith(BEARER_PREFIX):
            logger.warning("Requisição sem token em rota protegida: %s", request.path)
            raise UnauthorizedError("Token de autenticação ausente")

        payload = token_service.verify(header[len(BEARER_PREFIX) :])
        user = user_loader(payload.get("sub"))
        if user is None or not user.active:
            raise UnauthorizedError("Credenciais inválidas")

        g.current_user = user
        return user

    def require_auth(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            _authenticate()
            return view(*args, **kwargs)

        return wrapper

    def require_self_or_admin(view):
        """Permite que o usuário altere a própria conta; qualquer outra, só admin."""

        @wraps(view)
        def wrapper(*args, **kwargs):
            current = _authenticate()
            alvo = kwargs.get("user_id")
            if current.id != alvo and not current.is_admin():
                logger.warning(
                    "Usuário %s tentou alterar a conta %s", current.id, alvo
                )
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return wrapper

    def require_admin(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            current = _authenticate()
            if current.role != ROLE_ADMIN:
                raise ForbiddenError("Acesso negado")
            return view(*args, **kwargs)

        return wrapper

    return {
        "require_auth": require_auth,
        "require_self_or_admin": require_self_or_admin,
        "require_admin": require_admin,
    }
