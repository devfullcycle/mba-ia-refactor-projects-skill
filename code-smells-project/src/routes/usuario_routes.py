from flask import Blueprint, g, request

from src.controllers import usuario_controller
from src.middlewares.auth import admin_required, login_required
from src.utils.responses import sucesso

usuario_bp = Blueprint("usuarios", __name__)


@usuario_bp.get("/usuarios")
@admin_required
def listar_usuarios():
    return sucesso(usuario_controller.listar_usuarios())


@usuario_bp.get("/usuarios/<int:usuario_id>")
@login_required
def buscar_usuario(usuario_id):
    return sucesso(usuario_controller.obter_usuario(usuario_id, g.usuario))


@usuario_bp.post("/usuarios")
def criar_usuario():
    usuario_id = usuario_controller.criar_usuario(request.get_json(silent=True))
    return sucesso({"id": usuario_id}, status=201)


@usuario_bp.post("/login")
def login():
    usuario, token = usuario_controller.login(request.get_json(silent=True))
    return sucesso(usuario, mensagem="Login OK", token=token)
