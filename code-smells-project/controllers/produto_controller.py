from flask import request, jsonify
from models.produto_model import ProdutoModel
from config.settings import Config

class ProdutoController:
    @staticmethod
    def listar_produtos():
        produtos = ProdutoModel.listar_todos()
        return jsonify({"dados": produtos, "sucesso": True}), 200

    @staticmethod
    def buscar_produto(id):
        produto = ProdutoModel.buscar_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
        return jsonify({"dados": produto, "sucesso": True}), 200

    @staticmethod
    def buscar_produtos():
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        try:
            if preco_min is not None:
                preco_min = float(preco_min)
            if preco_max is not None:
                preco_max = float(preco_max)
        except ValueError:
            return jsonify({"erro": "Preço mínimo ou máximo inválido"}), 400

        resultados = ProdutoModel.buscar(
            termo=termo,
            categoria=categoria,
            preco_min=preco_min,
            preco_max=preco_max
        )
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    @staticmethod
    def criar_produto():
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        # Guard clauses com validações estruturadas
        campos_obrigatorios = ["nome", "preco", "estoque"]
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({"erro": f"{campo.capitalize()} é obrigatório"}), 400

        nome = str(dados.get("nome", "")).strip()
        descricao = str(dados.get("descricao", "")).strip()
        preco = dados.get("preco")
        estoque = dados.get("estoque")
        categoria = dados.get("categoria", "geral")

        if not isinstance(preco, (int, float)) or preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if not isinstance(estoque, int) or estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400
        if len(nome) < 2:
            return jsonify({"erro": "Nome muito curto"}), 400
        if len(nome) > 200:
            return jsonify({"erro": "Nome muito longo"}), 400
        if categoria not in Config.VALID_CATEGORIES:
            return jsonify({"erro": f"Categoria inválida. Válidas: {Config.VALID_CATEGORIES}"}), 400

        produto_id = ProdutoModel.criar(nome, descricao, float(preco), estoque, categoria)
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado"
        }), 201

    @staticmethod
    def atualizar_produto(id):
        produto_existente = ProdutoModel.buscar_por_id(id)
        if not produto_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        campos_obrigatorios = ["nome", "preco", "estoque"]
        for campo in campos_obrigatorios:
            if campo not in dados:
                return jsonify({"erro": f"{campo.capitalize()} é obrigatório"}), 400

        nome = str(dados.get("nome", "")).strip()
        descricao = str(dados.get("descricao", "")).strip()
        preco = dados.get("preco")
        estoque = dados.get("estoque")
        categoria = dados.get("categoria", "geral")

        if not isinstance(preco, (int, float)) or preco < 0:
            return jsonify({"erro": "Preço não pode ser negativo"}), 400
        if not isinstance(estoque, int) or estoque < 0:
            return jsonify({"erro": "Estoque não pode ser negativo"}), 400

        ProdutoModel.atualizar(id, nome, descricao, float(preco), int(estoque), categoria)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @staticmethod
    def deletar_produto(id):
        produto = ProdutoModel.buscar_por_id(id)
        if not produto:
            return jsonify({"erro": "Produto não encontrado"}), 404

        ProdutoModel.deletar(id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
