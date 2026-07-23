from flask import Blueprint, jsonify
from controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)


@pedido_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    body, status = pedido_controller.criar_pedido()
    return jsonify(body), status


@pedido_bp.route("/pedidos", methods=["GET"])
def listar_todos_pedidos():
    body, status = pedido_controller.listar_todos_pedidos()
    return jsonify(body), status


@pedido_bp.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
def listar_pedidos_usuario(usuario_id):
    body, status = pedido_controller.listar_pedidos_usuario(usuario_id)
    return jsonify(body), status


@pedido_bp.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
def atualizar_status_pedido(pedido_id):
    body, status = pedido_controller.atualizar_status_pedido(pedido_id)
    return jsonify(body), status
