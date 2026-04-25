import config.settings as settings
import models.order_model as order_model
import models.product_model as product_model
from services.notification_service import NotificationService


def create(dados):
    if not dados:
        return ({"erro": "Dados invalidos"}, 400)

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return ({"erro": "Usuario ID e obrigatorio"}, 400)
    if not itens:
        return ({"erro": "Pedido deve ter pelo menos 1 item"}, 400)

    product_ids = [item["produto_id"] for item in itens]
    product_lookup = product_model.get_by_ids(product_ids)

    for item in itens:
        product = product_lookup.get(item["produto_id"])
        if product is None:
            return ({"erro": f"Produto {item['produto_id']} nao encontrado", "sucesso": False}, 400)
        if product["estoque"] < item["quantidade"]:
            return ({"erro": f"Estoque insuficiente para {product['nome']}", "sucesso": False}, 400)

    resultado = order_model.create(usuario_id, itens, product_lookup)

    NotificationService.notify_new_order(resultado["pedido_id"], usuario_id)

    return ({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}, 201)


def list_all():
    pedidos = order_model.get_all()
    return ({"dados": pedidos, "sucesso": True}, 200)


def list_by_user(usuario_id):
    pedidos = order_model.get_by_user(usuario_id)
    return ({"dados": pedidos, "sucesso": True}, 200)


def update_status(pedido_id, dados):
    novo_status = dados.get("status", "")

    if novo_status not in settings.VALID_ORDER_STATUSES:
        return ({"erro": "Status invalido"}, 400)

    order_model.update_status(pedido_id, novo_status)

    NotificationService.notify_status_change(pedido_id, novo_status)

    return ({"sucesso": True, "mensagem": "Status atualizado"}, 200)
