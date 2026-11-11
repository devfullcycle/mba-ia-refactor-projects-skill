import hmac
from functools import wraps

from flask import current_app, g, request

from src.models import usuario_model
from src.services import auth_service
from src.utils.errors import ForbiddenError, UnauthorizedError

PREFIXO_BEARER = "Bearer "


def _autenticar_requisicao():
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith(PREFIXO_BEARER):
        raise UnauthorizedError("Token de acesso ausente (header Authorization: Bearer <token>)")

    try:
        usuario_id = auth_service.ler_usuario_id(cabecalho[len(PREFIXO_BEARER):].strip())
    except auth_service.TokenInvalidoError as exc:
        raise UnauthorizedError(str(exc))

    # Recarrega do banco: usuário removido ou rebaixado perde o acesso imediatamente.
    usuario = usuario_model.buscar_por_id(usuario_id)
    if usuario is None:
        raise UnauthorizedError("Token inválido")
    g.usuario = usuario
    return usuario


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        _autenticar_requisicao()
        return view(*args, **kwargs)

    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        usuario = _autenticar_requisicao()
        if usuario["tipo"] != usuario_model.TIPO_ADMIN:
            raise ForbiddenError("Acesso restrito a administradores")
        return view(*args, **kwargs)

    return wrapper


def admin_token_required(view):
    """Protege rotas de manutenção com o header X-Admin-Token (valor vindo de ADMIN_TOKEN)."""

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
