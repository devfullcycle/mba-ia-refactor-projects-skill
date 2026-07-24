"""Controller de Produto — orquestra validação e model, define status da resposta."""
import logging

from src.validators.produto_validator import validate_filtros_busca, validate_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produto_model):
        self._model = produto_model

    def listar(self):
        produtos = self._model.list_all()
        return {"dados": produtos, "sucesso": True}, 200

    def buscar(self, produto_id):
        produto = self._model.get_or_fail(produto_id)
        return {"dados": produto, "sucesso": True}, 200

    def pesquisar(self, args):
        filtros = validate_filtros_busca(args)
        resultados = self._model.search(**filtros)
        return {
            "dados": resultados,
            "total": len(resultados),
            "sucesso": True,
        }, 200

    def criar(self, dados):
        produto = validate_produto(dados)
        produto_id = self._model.create(**produto)
        logger.info("Produto criado", extra={"produto_id": produto_id})
        return {
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }, 201

    def atualizar(self, produto_id, dados):
        self._model.get_or_fail(produto_id)
        produto = validate_produto(dados)
        self._model.update(produto_id, **produto)
        logger.info("Produto atualizado", extra={"produto_id": produto_id})
        return {"sucesso": True, "mensagem": "Produto atualizado"}, 200

    def deletar(self, produto_id):
        self._model.get_or_fail(produto_id)
        self._model.delete(produto_id)
        logger.info("Produto removido", extra={"produto_id": produto_id})
        return {"sucesso": True, "mensagem": "Produto deletado"}, 200
