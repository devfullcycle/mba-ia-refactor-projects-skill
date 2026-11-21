"""Regra de negócio de pedidos: validação de estoque, total e persistência transacional."""
from middlewares.error_handler import AppError


class PedidoService:
    def __init__(self, pedido_model, produto_model):
        self._pedidos = pedido_model
        self._produtos = produto_model

    def criar(self, usuario_id, itens):
        produtos = self._produtos.buscar_por_ids([item["produto_id"] for item in itens])

        total = 0
        linhas = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise AppError("Produto " + str(item["produto_id"]) + " não encontrado", 400, {"sucesso": False})
            if produto["estoque"] < item["quantidade"]:
                raise AppError("Estoque insuficiente para " + produto["nome"], 400, {"sucesso": False})
            total = total + (produto["preco"] * item["quantidade"])
            linhas.append({
                "produto_id": item["produto_id"],
                "quantidade": item["quantidade"],
                "preco_unitario": produto["preco"],
            })

        pedido_id = self._pedidos.criar_com_itens(usuario_id, linhas, total)
        return {"pedido_id": pedido_id, "total": total}
