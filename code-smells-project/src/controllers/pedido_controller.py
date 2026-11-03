"""Fluxo dos casos de uso de Pedido e relatório de vendas."""
from collections import OrderedDict

from src.utils.errors import NotFoundError, ValidationError
from src.validators.pedido_validator import validar_novo_pedido, validar_status


class PedidoController:
    def __init__(self, pedido_model, produto_model, notification_service, transaction):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notificacoes = notification_service
        self._transaction = transaction

    def criar(self, dados):
        usuario_id, itens = validar_novo_pedido(dados)

        quantidades = OrderedDict()
        for item in itens:
            quantidades[item["produto_id"]] = quantidades.get(item["produto_id"], 0) + item["quantidade"]

        produtos = self._produtos.buscar_por_ids(list(quantidades))
        for produto_id, quantidade in quantidades.items():
            produto = produtos.get(produto_id)
            if produto is None:
                raise ValidationError(f"Produto {produto_id} não encontrado")
            if produto["estoque"] < quantidade:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")

        itens_com_preco = [
            {**item, "preco_unitario": produtos[item["produto_id"]]["preco"]} for item in itens
        ]
        total = sum(item["preco_unitario"] * item["quantidade"] for item in itens_com_preco)

        with self._transaction() as conn:
            pedido_id = self._pedidos.inserir(conn, usuario_id, total, itens_com_preco)
            for produto_id, quantidade in quantidades.items():
                if not self._produtos.baixar_estoque(conn, produto_id, quantidade):
                    raise ValidationError(f"Estoque insuficiente para {produtos[produto_id]['nome']}")

        self._notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self):
        return self._pedidos.listar()

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar(usuario_id=usuario_id)

    def atualizar_status(self, pedido_id, dados):
        novo_status = validar_status(dados)
        if not self._pedidos.existe(pedido_id):
            raise NotFoundError("Pedido não encontrado")
        self._pedidos.atualizar_status(pedido_id, novo_status)
        self._notificacoes.status_alterado(pedido_id, novo_status)

    def relatorio_vendas(self):
        return self._pedidos.resumo_vendas()
