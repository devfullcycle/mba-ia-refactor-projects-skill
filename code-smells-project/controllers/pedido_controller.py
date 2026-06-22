import logging
from flask import request, jsonify
import models.pedido_model as pedido_model
import models.relatorio_model as relatorio_model
from services.notification_service import notify_order_created, notify_order_status_changed
from config.settings import VALID_ORDER_STATUSES

logger = logging.getLogger(__name__)


def criar_pedido():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "usuario_id é obrigatório"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = pedido_model.criar_pedido(usuario_id, itens)

    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    notify_order_created(resultado["pedido_id"], usuario_id)
    logger.info("Pedido %d criado para usuário %d", resultado["pedido_id"], usuario_id)

    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_todos_pedidos():
    pedidos = pedido_model.get_todos_pedidos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_pedidos_usuario(usuario_id):
    pedidos = pedido_model.get_pedidos_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id):
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    novo_status = dados.get("status", "")
    if novo_status not in VALID_ORDER_STATUSES:
        return jsonify({"erro": f"Status inválido. Válidos: {VALID_ORDER_STATUSES}"}), 400

    pedido_model.atualizar_status_pedido(pedido_id, novo_status)
    notify_order_status_changed(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    relatorio = relatorio_model.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
