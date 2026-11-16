from exceptions import BusinessError, NotFoundError
from models import pedido_model, produto_model
from services import notificacao_service


def criar_pedido(usuario_id, itens):
    produtos = {}
    total = 0
    itens_precificados = []

    for item in itens:
        produto_id = item["produto_id"]
        if produto_id not in produtos:
            produtos[produto_id] = produto_model.buscar_por_id(produto_id)
        produto = produtos[produto_id]

        if produto is None:
            raise BusinessError("Produto " + str(produto_id) + " não encontrado")
        if produto["estoque"] < item["quantidade"]:
            raise BusinessError("Estoque insuficiente para " + produto["nome"])

        total = total + (produto["preco"] * item["quantidade"])
        itens_precificados.append((produto_id, item["quantidade"], produto["preco"]))

    pedido_id = pedido_model.criar(usuario_id, total, itens_precificados)
    notificacao_service.pedido_criado(pedido_id, usuario_id)
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    if not pedido_model.existe(pedido_id):
        raise NotFoundError("Pedido não encontrado")
    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.status_pedido_alterado(pedido_id, novo_status)
