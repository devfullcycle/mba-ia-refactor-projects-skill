from functools import wraps

from flask import current_app, g, request

from services.constantes import PERFIL_ADMIN
from services.excecoes import AppError


def _usuario_da_requisicao():
    cabecalho = request.headers.get("Authorization", "")
    if not cabecalho.startswith("Bearer "):
        return None
    token = cabecalho[len("Bearer "):].strip()
    if not token:
        return None
    return current_app.extensions["servicos"].auth.usuario_do_token(token)


def requer_autenticacao(*perfis):
    """Exige token válido (401) e, se informados, um dos perfis (403). Define g.usuario."""
    def decorador(funcao):
        @wraps(funcao)
        def envolvida(*args, **kwargs):
            usuario = _usuario_da_requisicao()
            if usuario is None:
                raise AppError("Não autenticado", 401)
            if perfis and usuario["tipo"] not in perfis:
                raise AppError("Sem permissão", 403)
            g.usuario = usuario
            return funcao(*args, **kwargs)
        return envolvida
    return decorador


def garantir_dono_ou_admin(usuario_id):
    usuario = g.usuario
    if usuario["tipo"] != PERFIL_ADMIN and usuario["id"] != usuario_id:
        raise AppError("Sem permissão", 403)
