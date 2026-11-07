from flask import request, jsonify

from config.settings import Config


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    @staticmethod
    def _validar(dados):
        """Validação central de produto. Retorna mensagem de erro ou None."""
        if not dados:
            return "Dados inválidos"
        for campo in ("nome", "preco", "estoque"):
            if campo not in dados:
                return f"{campo.capitalize()} é obrigatório"
        if dados["preco"] < 0:
            return "Preço não pode ser negativo"
        if dados["estoque"] < 0:
            return "Estoque não pode ser negativo"
        nome = dados["nome"]
        if len(nome) < 2:
            return "Nome muito curto"
        if len(nome) > 200:
            return "Nome muito longo"
        categoria = dados.get("categoria", "geral")
        if categoria not in Config.CATEGORIAS_VALIDAS:
            return "Categoria inválida. Válidas: " + str(Config.CATEGORIAS_VALIDAS)
        return None

    def listar(self):
        produtos = self._produtos.list()
        return jsonify({"dados": produtos, "sucesso": True}), 200

    def buscar(self, id):
        produto = self._produtos.get(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404

    def buscar_produtos(self):
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)
        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)
        resultados = self._produtos.search(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def criar(self):
        dados = request.get_json()
        erro = self._validar(dados)
        if erro:
            return jsonify({"erro": erro}), 400
        novo_id = self._produtos.create(
            dados["nome"], dados.get("descricao", ""), dados["preco"],
            dados["estoque"], dados.get("categoria", "geral"),
        )
        return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    def atualizar(self, id):
        if not self._produtos.get(id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        dados = request.get_json()
        erro = self._validar(dados)
        if erro:
            return jsonify({"erro": erro}), 400
        self._produtos.update(
            id, dados["nome"], dados.get("descricao", ""), dados["preco"],
            dados["estoque"], dados.get("categoria", "geral"),
        )
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        if not self._produtos.get(id):
            return jsonify({"erro": "Produto não encontrado"}), 404
        self._produtos.delete(id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
