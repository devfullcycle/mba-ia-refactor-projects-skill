from flask import jsonify
from models import produto
from utils.validators import validar_produto
from utils.logger import get_logger

logger = get_logger(__name__)

def listar():
    try:
        produtos_list = produto.listar_todos()
        logger.info(f"Listando {len(produtos_list)} produtos")
        return jsonify({"dados": produtos_list, "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        return jsonify({"erro": "Erro ao listar produtos"}), 500

def buscar_por_id(id):
    try:
        prod = produto.buscar_por_id(id)
        if prod:
            return jsonify({"dados": prod, "sucesso": True}), 200
        else:
            return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception as e:
        logger.error(f"Erro ao buscar produto: {str(e)}")
        return jsonify({"erro": "Erro ao buscar produto"}), 500

def criar(dados):
    try:
        erros = validar_produto(dados)
        if erros:
            return jsonify({"erros": erros}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        id = produto.criar(nome, descricao, preco, estoque, categoria)
        logger.info(f"Produto criado com ID: {id}")
        return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    except Exception as e:
        logger.error(f"Erro ao criar produto: {str(e)}")
        return jsonify({"erro": "Erro ao criar produto"}), 500

def atualizar(id, dados):
    try:
        prod_existente = produto.buscar_por_id(id)
        if not prod_existente:
            return jsonify({"erro": "Produto não encontrado"}), 404

        erros = validar_produto(dados)
        if erros:
            return jsonify({"erros": erros}), 400

        nome = dados["nome"]
        descricao = dados.get("descricao", "")
        preco = dados["preco"]
        estoque = dados["estoque"]
        categoria = dados.get("categoria", "geral")

        produto.atualizar(id, nome, descricao, preco, estoque, categoria)
        logger.info(f"Produto {id} atualizado")
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    except Exception as e:
        logger.error(f"Erro ao atualizar produto: {str(e)}")
        return jsonify({"erro": "Erro ao atualizar produto"}), 500

def deletar(id):
    try:
        prod = produto.buscar_por_id(id)
        if not prod:
            return jsonify({"erro": "Produto não encontrado"}), 404

        produto.deletar(id)
        logger.info(f"Produto {id} deletado")
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except Exception as e:
        logger.error(f"Erro ao deletar produto: {str(e)}")
        return jsonify({"erro": "Erro ao deletar produto"}), 500

def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    try:
        resultados = produto.buscar(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {str(e)}")
        return jsonify({"erro": "Erro ao buscar produtos"}), 500
