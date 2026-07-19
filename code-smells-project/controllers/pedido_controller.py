"""Controller de Pedidos — orquestra validação, model e notificações."""
from flask import jsonify, request

from models import pedido_model
from services import notificacao_service

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


def criar():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens or len(itens) == 0:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = pedido_model.criar(usuario_id, itens)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    notificacao_service.notificar_pedido_criado(resultado["pedido_id"], usuario_id)
    return jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201


def listar_por_usuario(usuario_id):
    pedidos = pedido_model.listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos():
    pedidos = pedido_model.listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status(pedido_id):
    dados = request.get_json()
    novo_status = dados.get("status", "")

    if novo_status not in STATUS_VALIDOS:
        return jsonify({"erro": "Status inválido"}), 400

    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.notificar_status_pedido(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
