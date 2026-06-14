from flask import Blueprint, request, jsonify
from database import get_db
from models.order_model import OrderModel
from controllers.order_controller import OrderController

pedidos_bp = Blueprint("pedidos", __name__)


def _controller():
    return OrderController(OrderModel(get_db()))


@pedidos_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    result, status = _controller().create(request.get_json())
    return jsonify(result), status


@pedidos_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    result, status = _controller().list_all()
    return jsonify(result), status


@pedidos_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    result, status = _controller().list_by_user(usuario_id)
    return jsonify(result), status


@pedidos_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    result, status = _controller().update_status(pedido_id, request.get_json())
    return jsonify(result), status


@pedidos_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    result, status = _controller().sales_report()
    return jsonify(result), status
