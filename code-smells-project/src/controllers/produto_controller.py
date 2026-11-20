import logging
from typing import Optional

from ..models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS, ProdutoModel
from .errors import NotFoundError
from .validators import parse_optional_float, validar_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produtos: ProdutoModel):
        self.produtos = produtos

    def listar(self) -> list:
        return self.produtos.listar()

    def obter(self, produto_id: int) -> dict:
        produto = self.produtos.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado")
        return produto

    def criar(self, dados) -> int:
        produto = validar_produto(dados, CATEGORIAS_VALIDAS, CATEGORIA_PADRAO)
        produto_id = self.produtos.criar(**produto)
        logger.info("Produto criado id=%s", produto_id)
        return produto_id

    def atualizar(self, produto_id: int, dados) -> None:
        self.obter(produto_id)
        produto = validar_produto(dados, CATEGORIAS_VALIDAS, CATEGORIA_PADRAO)
        self.produtos.atualizar(produto_id, **produto)

    def deletar(self, produto_id: int) -> None:
        self.obter(produto_id)
        self.produtos.deletar(produto_id)
        logger.info("Produto deletado id=%s", produto_id)

    def buscar(self, termo: str, categoria: Optional[str], preco_min: Optional[str], preco_max: Optional[str]) -> list:
        return self.produtos.buscar(
            termo,
            categoria,
            parse_optional_float(preco_min, "preco_min"),
            parse_optional_float(preco_max, "preco_max"),
        )
