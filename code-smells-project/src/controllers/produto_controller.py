"""Fluxo dos casos de uso de Produto."""
import logging

from src.utils.errors import NotFoundError
from src.validators.produto_validator import parse_filtro_preco, validar_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self):
        produtos = self._produtos.listar()
        logger.debug("Listando %d produtos", len(produtos))
        return produtos

    def obter(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if not produto:
            raise NotFoundError("Produto não encontrado")
        return produto

    def pesquisar(self, filtros):
        return self._produtos.pesquisar(
            termo=filtros.get("q", ""),
            categoria=filtros.get("categoria") or None,
            preco_min=parse_filtro_preco("preco_min", filtros.get("preco_min")),
            preco_max=parse_filtro_preco("preco_max", filtros.get("preco_max")),
        )

    def criar(self, dados):
        produto = validar_produto(dados)
        produto_id = self._produtos.criar(**produto)
        logger.info("Produto criado com ID: %s", produto_id)
        return produto_id

    def atualizar(self, produto_id, dados):
        self.obter(produto_id)
        produto = validar_produto(dados)
        self._produtos.atualizar(produto_id, **produto)

    def deletar(self, produto_id):
        self.obter(produto_id)
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
