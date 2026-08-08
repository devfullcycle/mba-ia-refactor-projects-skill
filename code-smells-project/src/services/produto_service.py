"""Produto business rules and validation."""

from __future__ import annotations

import logging
from typing import Any

from src.config.settings import CATEGORIAS_VALIDAS
from src.models.produto_model import ProdutoModel
from src.services.errors import DomainError, NotFoundError

logger = logging.getLogger(__name__)


class ProdutoService:
    def __init__(self, model: ProdutoModel) -> None:
        self._model = model

    def listar(self) -> list[dict[str, Any]]:
        produtos = self._model.listar_todos()
        logger.info("Listando %s produtos", len(produtos))
        return produtos

    def buscar_por_id(self, produto_id: int) -> dict[str, Any]:
        produto = self._model.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto

    def criar(self, dados: dict[str, Any]) -> int:
        payload = self._validar_payload(dados)
        produto_id = self._model.criar(**payload)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id: int, dados: dict[str, Any]) -> None:
        if not self._model.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        payload = self._validar_payload(dados)
        self._model.atualizar(produto_id, **payload)

    def deletar(self, produto_id: int) -> None:
        if not self._model.buscar_por_id(produto_id):
            raise NotFoundError("Produto não encontrado")
        self._model.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)

    def buscar(
        self,
        termo: str = "",
        categoria: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> list[dict[str, Any]]:
        return self._model.buscar(termo, categoria, preco_min, preco_max)

    def _validar_payload(self, dados: dict[str, Any] | None) -> dict[str, Any]:
        if not dados:
            raise DomainError("Dados inválidos")
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                label = {"nome": "Nome", "preco": "Preço", "estoque": "Estoque"}[campo]
                raise DomainError(f"{label} é obrigatório")

        nome = str(dados["nome"])
        descricao = str(dados.get("descricao", ""))
        try:
            preco = float(dados["preco"])
            estoque = int(dados["estoque"])
        except (TypeError, ValueError) as exc:
            raise DomainError("Preço ou estoque inválidos") from exc

        categoria = str(dados.get("categoria", "geral"))

        if preco < 0:
            raise DomainError("Preço não pode ser negativo")
        if estoque < 0:
            raise DomainError("Estoque não pode ser negativo")
        if len(nome) < 2:
            raise DomainError("Nome muito curto")
        if len(nome) > 200:
            raise DomainError("Nome muito longo")
        if categoria not in CATEGORIAS_VALIDAS:
            raise DomainError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")

        return {
            "nome": nome,
            "descricao": descricao,
            "preco": preco,
            "estoque": estoque,
            "categoria": categoria,
        }
