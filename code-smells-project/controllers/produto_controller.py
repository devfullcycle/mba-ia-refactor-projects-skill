"""Fluxo da aplicação para o domínio de produtos (orquestra service + resposta)."""

from flask import jsonify, request
from services import produto_service
from middlewares.error_handler import api_error_handler


@api_error_handler
def listar_produtos():
    produtos = produto_service.listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


@api_error_handler
def buscar_produto(produto_id):
    produto = produto_service.obter(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


@api_error_handler
def criar_produto():
    dados = request.get_json()
    novo_id = produto_service.criar(dados)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


@api_error_handler
def atualizar_produto(produto_id):
    dados = request.get_json()
    produto_service.atualizar(produto_id, dados)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


@api_error_handler
def deletar_produto(produto_id):
    produto_service.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


@api_error_handler
def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = _opt_float(request.args.get("preco_min"))
    preco_max = _opt_float(request.args.get("preco_max"))
    resultados = produto_service.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200


def _opt_float(valor):
    try:
        return float(valor) if valor is not None else None
    except (TypeError, ValueError):
        return None