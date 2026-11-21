from flask import jsonify, request

from services.notificacao_service import notificar_pedido_criado, notificar_status_pedido
from validators import validar_novo_pedido, validar_status_pedido


class PedidoController:
    def __init__(self, pedido_model, pedido_service):
        self._pedidos = pedido_model
        self._service = pedido_service

    def criar(self):
        dados = validar_novo_pedido(request.get_json(silent=True))
        resultado = self._service.criar(dados["usuario_id"], dados["itens"])
        notificar_pedido_criado(resultado["pedido_id"], dados["usuario_id"])
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_por_usuario(self, usuario_id):
        return jsonify({"dados": self._pedidos.listar(usuario_id), "sucesso": True}), 200

    def listar_todos(self):
        return jsonify({"dados": self._pedidos.listar(), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        novo_status = validar_status_pedido(request.get_json(silent=True))
        self._pedidos.atualizar_status(pedido_id, novo_status)
        notificar_status_pedido(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
