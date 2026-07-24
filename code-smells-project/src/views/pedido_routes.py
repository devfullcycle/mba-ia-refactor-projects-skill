"""Rotas de Pedido."""
from flask import Blueprint, jsonify, request


def create_pedido_blueprint(controller):
    blueprint = Blueprint("pedidos", __name__)

    @blueprint.route("/pedidos", methods=["POST"])
    def criar_pedido():
        body, status = controller.criar(request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/pedidos", methods=["GET"])
    def listar_todos_pedidos():
        body, status = controller.listar_todos()
        return jsonify(body), status

    @blueprint.route("/pedidos/usuario/<int:usuario_id>", methods=["GET"])
    def listar_pedidos_usuario(usuario_id):
        body, status = controller.listar_por_usuario(usuario_id)
        return jsonify(body), status

    @blueprint.route("/pedidos/<int:pedido_id>/status", methods=["PUT"])
    def atualizar_status_pedido(pedido_id):
        body, status = controller.atualizar_status(
            pedido_id, request.get_json(silent=True)
        )
        return jsonify(body), status

    return blueprint
