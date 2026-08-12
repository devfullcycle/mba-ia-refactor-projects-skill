"""Endpoints HTTP do domínio de pedidos e relatórios."""

from flask import Blueprint
from controllers import pedido_controller

pedidos_bp = Blueprint("pedidos", __name__)

pedidos_bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar_pedido, methods=["POST"])
pedidos_bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos_pedidos, methods=["GET"])
pedidos_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_pedidos_usuario",
    pedido_controller.listar_pedidos_usuario,
    methods=["GET"],
)
pedidos_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status_pedido",
    pedido_controller.atualizar_status_pedido,
    methods=["PUT"],
)
pedidos_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", pedido_controller.relatorio_vendas, methods=["GET"])