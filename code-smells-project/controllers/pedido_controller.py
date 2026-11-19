from flask import request, jsonify

from config.settings import Config


class PedidoController:
    def __init__(self, pedido_service):
        self._service = pedido_service

    def criar(self):
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])
        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = self._service.criar(usuario_id, itens)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_todos(self):
        return jsonify({"dados": self._service.listar(), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        return jsonify({"dados": self._service.listar(usuario_id), "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        dados = request.get_json()
        novo_status = dados.get("status", "")
        if novo_status not in Config.STATUS_PEDIDO_VALIDOS:
            return jsonify({"erro": "Status inválido"}), 400
        self._service.atualizar_status(pedido_id, novo_status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
