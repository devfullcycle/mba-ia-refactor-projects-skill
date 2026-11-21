import logging

from flask import jsonify, request

from middlewares.error_handler import AppError
from validators import validar_filtros_busca, validar_produto

logger = logging.getLogger(__name__)


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def _obter_ou_404(self, produto_id, extra=None):
        produto = self._produtos.buscar_por_id(produto_id)
        if not produto:
            raise AppError("Produto não encontrado", 404, extra)
        return produto

    def listar(self):
        produtos = self._produtos.listar()
        logger.info("Listando %s produtos", len(produtos))
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar(self, produto_id):
        produto = self._obter_ou_404(produto_id, {"sucesso": False})
        return jsonify({"dados": produto, "sucesso": True}), 200

    def criar(self):
        dados = validar_produto(request.get_json(silent=True))
        produto_id = self._produtos.criar(**dados)
        logger.info("Produto criado com ID: %s", produto_id)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, produto_id):
        self._obter_ou_404(produto_id)
        dados = validar_produto(request.get_json(silent=True))
        self._produtos.atualizar(produto_id, **dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, produto_id):
        self._obter_ou_404(produto_id)
        self._produtos.deletar(produto_id)
        logger.info("Produto %s deletado", produto_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    def buscar_por_filtros(self):
        filtros = validar_filtros_busca(request.args)
        resultados = self._produtos.buscar(**filtros)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
