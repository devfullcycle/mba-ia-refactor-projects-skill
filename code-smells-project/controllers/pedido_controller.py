import logging
from flask import request, jsonify
from models.pedido_model import PedidoModel
from config.settings import Config

logger = logging.getLogger(__name__)

class PedidoController:
    @staticmethod
    def criar_pedido():
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or not isinstance(itens, list) or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = PedidoModel.criar(usuario_id, itens)
        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        logger.info(f"Pedido {resultado['pedido_id']} criado para usuario {usuario_id}")
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201

    @staticmethod
    def listar_todos_pedidos():
        pedidos = PedidoModel.listar_todos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @staticmethod
    def listar_pedidos_usuario(usuario_id):
        pedidos = PedidoModel.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    @staticmethod
    def atualizar_status_pedido(pedido_id):
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        novo_status = dados.get("status", "")
        if novo_status not in Config.VALID_ORDER_STATUSES:
            return jsonify({"erro": "Status inválido"}), 400

        atualizado = PedidoModel.atualizar_status(pedido_id, novo_status)
        if not atualizado:
            return jsonify({"erro": "Pedido não encontrado"}), 404

        logger.info(f"Status do pedido {pedido_id} alterado para {novo_status}")
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
