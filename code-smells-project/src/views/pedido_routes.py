from flask import Blueprint, jsonify, request

from ..controllers.pedido_controller import PedidoController


def build_pedido_routes(controller: PedidoController) -> Blueprint:
    bp = Blueprint("pedidos", __name__)

    @bp.post("/pedidos")
    def criar_pedido():
        resultado = controller.criar(request.get_json(silent=True))
        return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @bp.get("/pedidos")
    def listar_todos_pedidos():
        return jsonify({"dados": controller.listar_todos(), "sucesso": True}), 200

    @bp.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        return jsonify({"dados": controller.listar_por_usuario(usuario_id), "sucesso": True}), 200

    @bp.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        controller.atualizar_status(pedido_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    return bp
