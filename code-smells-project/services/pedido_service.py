from decimal import Decimal

from models.pedido_model import EstoqueInsuficiente
from services.dinheiro import arredondar, para_decimal
from services.excecoes import AppError


class PedidoService:
    def __init__(self, pedidos, produtos, usuarios, notificacoes):
        self._pedidos = pedidos
        self._produtos = produtos
        self._usuarios = usuarios
        self._notificacoes = notificacoes

    def criar(self, usuario_id, itens):
        if self._usuarios.buscar_por_id(usuario_id) is None:
            raise AppError("Usuário não encontrado")
        produtos = self._produtos.buscar_por_ids([item["produto_id"] for item in itens])

        total = Decimal("0")
        itens_com_preco = []
        for item in itens:
            produto = produtos.get(item["produto_id"])
            if produto is None:
                raise AppError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise AppError(f"Estoque insuficiente para {produto['nome']}")
            total += para_decimal(produto["preco"]) * item["quantidade"]
            itens_com_preco.append({**item, "preco_unitario": produto["preco"]})

        total = arredondar(total)
        try:
            pedido_id = self._pedidos.criar(usuario_id, itens_com_preco, total)
        except EstoqueInsuficiente as erro:
            raise AppError(f"Estoque insuficiente para {produtos[erro.produto_id]['nome']}") from None

        self._notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self):
        return self._pedidos.listar()

    def listar_do_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id, status):
        if not self._pedidos.atualizar_status(pedido_id, status):
            raise AppError("Pedido não encontrado", 404)
        self._notificacoes.status_alterado(pedido_id, status)
