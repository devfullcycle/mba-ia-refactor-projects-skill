from flask import Blueprint, g, request

from src.controllers import pedido_controller
from src.middlewares.auth import admin_required, login_required
from src.utils.responses import sucesso

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.post("/pedidos")
@login_required
def criar_pedido():
    resultado = pedido_controller.criar_pedido(request.get_json(silent=True), g.usuario)
    return sucesso(resultado, status=201, mensagem="Pedido criado com sucesso")


@pedido_bp.get("/pedidos")
@admin_required
def listar_todos_pedidos():
    return sucesso(pedido_controller.listar_todos_pedidos())


@pedido_bp.get("/pedidos/usuario/<int:usuario_id>")
@login_required
def listar_pedidos_usuario(usuario_id):
    return sucesso(pedido_controller.listar_pedidos_usuario(usuario_id, g.usuario))


@pedido_bp.put("/pedidos/<int:pedido_id>/status")
@admin_required
def atualizar_status_pedido(pedido_id):
    pedido_controller.atualizar_status_pedido(pedido_id, request.get_json(silent=True))
    return sucesso(mensagem="Status atualizado")
