class PedidoService:
    """Regra de negócio de pedidos (antes presa dentro de model/controller)."""

    def __init__(self, pedido_model, produto_model, notifier):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notifier = notifier

    def criar(self, usuario_id, itens):
        ids = [item["produto_id"] for item in itens]
        produtos = self._produtos.get_by_ids(ids)  # uma query só

        total = 0
        linhas = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                return {"erro": f"Produto {item['produto_id']} não encontrado"}
            if produto["estoque"] < item["quantidade"]:
                return {"erro": f"Estoque insuficiente para {produto['nome']}"}
            total += produto["preco"] * item["quantidade"]
            linhas.append((item["produto_id"], item["quantidade"], produto["preco"]))

        pedido_id = self._pedidos.criar(usuario_id, total, linhas)
        self._notifier.pedido_criado(usuario_id, pedido_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar(self, usuario_id=None):
        return self._pedidos.listar(usuario_id)

    def atualizar_status(self, pedido_id, novo_status):
        self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notifier.status_alterado(pedido_id, novo_status)
        return True
