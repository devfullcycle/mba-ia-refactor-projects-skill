import logging
from flask import request, jsonify
import models.produto_model as produto_model
from config.settings import VALID_CATEGORIES

logger = logging.getLogger(__name__)


def _validate_produto_input(dados):
    if not dados:
        return "Dados inválidos"
    nome = dados.get("nome", "")
    preco = dados.get("preco")
    estoque = dados.get("estoque")
    categoria = dados.get("categoria", "geral")

    if not nome:
        return "Nome é obrigatório"
    if len(nome) < 2:
        return "Nome muito curto"
    if len(nome) > 200:
        return "Nome muito longo"
    if preco is None:
        return "Preço é obrigatório"
    if estoque is None:
        return "Estoque é obrigatório"
    if preco < 0:
        return "Preço não pode ser negativo"
    if estoque < 0:
        return "Estoque não pode ser negativo"
    if categoria not in VALID_CATEGORIES:
        return f"Categoria inválida. Válidas: {VALID_CATEGORIES}"
    return None


def listar_produtos():
    produtos = produto_model.get_todos_produtos()
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria") or None
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")

    try:
        preco_min = float(preco_min) if preco_min else None
        preco_max = float(preco_max) if preco_max else None
    except ValueError:
        return jsonify({"erro": "Parâmetros de preço inválidos"}), 400

    resultados = produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def buscar_produto(id):
    produto = produto_model.get_produto_por_id(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto():
    dados = request.get_json()
    erro = _validate_produto_input(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_id = produto_model.criar_produto(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    logger.info("Produto criado com ID: %d", produto_id)
    return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    produto_existente = produto_model.get_produto_por_id(id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json()
    erro = _validate_produto_input(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.atualizar_produto(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    produto = produto_model.get_produto_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_model.deletar_produto(id)
    logger.info("Produto %d desativado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto removido"}), 200
