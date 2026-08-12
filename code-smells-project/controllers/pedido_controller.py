"""Fluxo da aplicação para o domínio de pedidos e relatórios."""

from flask import jsonify, request
from services import pedido_service
from middlewares.error_handler import api_error_handler


@api_error_handler
def criar_pedido():
    dados = request.get_json() or {}
    resultado = pedido_service.processar_criacao(dados.get("usuario_id"), dados.get("itens"))
    return jsonify(
        {"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}
    ), 201


@api_error_handler
def listar_pedidos_usuario(usuario_id):
    pedidos = _listar_pedidos(usuario_id=usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@api_error_handler
def listar_todos_pedidos():
    pedidos = _listar_pedidos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


@api_error_handler
def atualizar_status_pedido(pedido_id):
    dados = request.get_json() or {}
    novo_status = dados.get("status", "")
    pedido_service.atualizar_status(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


@api_error_handler
def relatorio_vendas():
    relatorio = pedido_service.relatorio_vendas_com_desconto()
    return jsonify({"dados": relatorio, "sucesso": True}), 200


def _listar_pedidos(usuario_id=None):
    from models import pedido_model

    if usuario_id is not None:
        return pedido_model.get_pedidos_por_usuario(usuario_id)
    return pedido_model.get_todos_pedidos()