from functools import wraps

from flask import g, request

from src.models import user as user_model
from src.services import auth_service
from src.utils.errors import ForbiddenError, UnauthorizedError

BEARER_PREFIX = "Bearer "


def _authenticate_request():
    header = request.headers.get("Authorization", "")
    if not header.startswith(BEARER_PREFIX):
        raise UnauthorizedError("Token de acesso ausente (header Authorization: Bearer <token>)")

    try:
        user_id = auth_service.read_user_id(header[len(BEARER_PREFIX):].strip())
    except auth_service.InvalidTokenError as exc:
        raise UnauthorizedError(str(exc))

    # Recarrega do banco: usuário removido, desativado ou rebaixado perde o acesso na hora.
    user = user_model.find_by_id(user_id) if isinstance(user_id, int) else None
    if user is None or not user.active:
        raise UnauthorizedError("Token inválido")
    g.current_user = user
    return user


def current_user():
    return g.get("current_user")


def optional_auth():
    """Autentica se houver header Authorization; usado no cadastro público de usuários."""
    if request.headers.get("Authorization"):
        return _authenticate_request()
    return None


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        _authenticate_request()
        return view(*args, **kwargs)

    return wrapper


def roles_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _authenticate_request()
            if user.role not in roles:
                raise ForbiddenError("Acesso não permitido para este perfil")
            return view(*args, **kwargs)

        return wrapper

    return decorator


admin_required = roles_required(user_model.ROLE_ADMIN)
staff_required = roles_required(*user_model.STAFF_ROLES)
