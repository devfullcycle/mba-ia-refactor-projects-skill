from flask import Blueprint, request, jsonify
from controllers import order_controller
from middlewares.error_handler import handle_errors

bp = Blueprint("pedidos", __name__)


@bp.route("/pedidos", methods=["POST"])
@handle_errors
def criar_pedido():
    dados = request.get_json()
    result, status = order_controller.create(dados)
    return jsonify(result), status


@bp.route("/pedidos", methods=["GET"])
@handle_errors
def listar_todos_pedidos():
    result, status = order_controller.list_all()
    return jsonify(result), status


@bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
@handle_errors
def listar_pedidos_usuario(usuario_id):
    result, status = order_controller.list_by_user(usuario_id)
    return jsonify(result), status


@bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
@handle_errors
def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    result, status = order_controller.update_status(pedido_id, dados)
    return jsonify(result), status
