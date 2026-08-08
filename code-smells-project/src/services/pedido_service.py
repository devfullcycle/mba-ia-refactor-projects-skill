"""Pedido business rules: stock, totals, status transitions."""

from __future__ import annotations

import logging
from typing import Any

from src.config.settings import STATUS_PEDIDO_VALIDOS
from src.models.pedido_model import PedidoModel
from src.services.errors import DomainError
from src.services.notificacao_service import NotificacaoService

logger = logging.getLogger(__name__)


class PedidoService:
    def __init__(
        self,
        model: PedidoModel,
        notificacoes: NotificacaoService | None = None,
    ) -> None:
        self._model = model
        self._notificacoes = notificacoes or NotificacaoService()

    def listar_todos(self) -> list[dict[str, Any]]:
        return self._model.listar_todos()

    def listar_por_usuario(self, usuario_id: int) -> list[dict[str, Any]]:
        return self._model.listar_por_usuario(usuario_id)

    def criar(self, dados: dict[str, Any] | None) -> dict[str, Any]:
        if not dados:
            raise DomainError("Dados inválidos")

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens") or []

        if not usuario_id:
            raise DomainError("Usuario ID é obrigatório")
        if not itens:
            raise DomainError("Pedido deve ter pelo menos 1 item")

        try:
            usuario_id = int(usuario_id)
        except (TypeError, ValueError) as exc:
            raise DomainError("Usuario ID inválido") from exc

        linhas: list[tuple[int, int, float]] = []
        total = 0.0

        for item in itens:
            try:
                produto_id = int(item["produto_id"])
                quantidade = int(item["quantidade"])
            except (KeyError, TypeError, ValueError) as exc:
                raise DomainError("Item de pedido inválido") from exc

            if quantidade <= 0:
                raise DomainError("Quantidade deve ser positiva")

            produto = self._model.produto_para_pedido(produto_id)
            if produto is None:
                raise DomainError(f"Produto {produto_id} não encontrado")
            if produto["estoque"] < quantidade:
                raise DomainError(f"Estoque insuficiente para {produto['nome']}")

            preco = float(produto["preco"])
            total += preco * quantidade
            linhas.append((produto_id, quantidade, preco))

        pedido_id = self._model.criar(usuario_id, total)
        for produto_id, quantidade, preco in linhas:
            self._model.adicionar_item(pedido_id, produto_id, quantidade, preco)
            self._model.decrementar_estoque(produto_id, quantidade)
        self._model.commit()

        resultado = {"pedido_id": pedido_id, "total": total}
        self._notificacoes.pedido_criado(pedido_id, usuario_id)
        return resultado

    def atualizar_status(self, pedido_id: int, dados: dict[str, Any] | None) -> None:
        if not dados:
            raise DomainError("Dados inválidos")

        novo_status = str(dados.get("status", ""))
        if novo_status not in STATUS_PEDIDO_VALIDOS:
            raise DomainError("Status inválido")

        self._model.atualizar_status(pedido_id, novo_status)
        self._notificacoes.status_atualizado(pedido_id, novo_status)
