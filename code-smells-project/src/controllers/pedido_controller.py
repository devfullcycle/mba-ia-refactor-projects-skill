import logging

from ..models.pedido_model import (
    STATUS_APROVADO,
    STATUS_CANCELADO,
    STATUS_VALIDOS,
    EstoqueInsuficienteError,
    PedidoModel,
)
from ..models.produto_model import ProdutoModel
from ..services.notification_service import NotificationService
from .errors import NotFoundError, ValidationError
from .validators import validar_pedido, validar_status

logger = logging.getLogger(__name__)


class PedidoController:
    def __init__(self, pedidos: PedidoModel, produtos: ProdutoModel, notificacoes: NotificationService):
        self.pedidos = pedidos
        self.produtos = produtos
        self.notificacoes = notificacoes

    def criar(self, dados) -> dict:
        pedido = validar_pedido(dados)
        catalogo = self.produtos.buscar_por_ids(item["produto_id"] for item in pedido["itens"])

        itens, total = [], 0
        for item in pedido["itens"]:
            produto = catalogo.get(item["produto_id"])
            if produto is None:
                raise ValidationError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValidationError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
            itens.append({**item, "preco_unitario": produto["preco"]})

        try:
            pedido_id = self.pedidos.criar(pedido["usuario_id"], total, itens)
        except EstoqueInsuficienteError as erro:
            raise ValidationError(f"Estoque insuficiente para {catalogo[erro.produto_id]['nome']}") from None

        self.notificacoes.pedido_criado(pedido_id, pedido["usuario_id"])
        return {"pedido_id": pedido_id, "total": total}

    def listar_todos(self) -> list:
        return self.pedidos.listar_todos()

    def listar_por_usuario(self, usuario_id: int) -> list:
        return self.pedidos.listar_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id: int, dados) -> None:
        status = validar_status(dados, STATUS_VALIDOS)
        if not self.pedidos.existe(pedido_id):
            raise NotFoundError("Pedido não encontrado")
        self.pedidos.atualizar_status(pedido_id, status)

        if status == STATUS_APROVADO:
            self.notificacoes.pedido_aprovado(pedido_id)
        elif status == STATUS_CANCELADO:
            self.notificacoes.pedido_cancelado(pedido_id)
