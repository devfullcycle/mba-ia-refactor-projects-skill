"""Pedido HTTP controllers."""

from __future__ import annotations

from flask import jsonify, request

from src.controllers.deps import pedido_service


def criar_pedido():
    resultado = pedido_service().criar(request.get_json(silent=True))
    return jsonify(
        {
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }
    ), 201


def listar_pedidos_usuario(usuario_id: int):
    pedidos = pedido_service().listar_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos():
    pedidos = pedido_service().listar_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id: int):
    pedido_service().atualizar_status(pedido_id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
