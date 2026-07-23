from flask import request
from core.constants import STATUS_PEDIDO
from core.errors import ValidationError
from services import pedido_service


def criar_pedido():
    data = request.get_json() or {}
    usuario_id = data.get("usuario_id")
    itens = data.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID e obrigatorio")
    resultado = pedido_service.create_order(usuario_id, itens)
    return (
        {
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        },
        201,
    )


def listar_pedidos_usuario(usuario_id):
    return {"dados": pedido_service.list_orders_by_user(usuario_id), "sucesso": True}, 200


def listar_todos_pedidos():
    return {"dados": pedido_service.list_all_orders(), "sucesso": True}, 200


def atualizar_status_pedido(pedido_id):
    data = request.get_json() or {}
    novo_status = data.get("status", "")
    if novo_status not in STATUS_PEDIDO:
        raise ValidationError("Status invalido")
    pedido_service.update_order_status(pedido_id, novo_status)
    return {"sucesso": True, "mensagem": "Status atualizado"}, 200
