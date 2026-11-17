from flask import Blueprint
from controllers.pedido_controller import PedidoController

pedido_bp = Blueprint("pedidos", __name__)

pedido_bp.route("/pedidos", methods=["POST"])(PedidoController.criar_pedido)
pedido_bp.route("/pedidos", methods=["GET"])(PedidoController.listar_todos_pedidos)
pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])(PedidoController.listar_pedidos_usuario)
pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])(PedidoController.atualizar_status_pedido)
