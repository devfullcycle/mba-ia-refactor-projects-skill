import logging

from flask import jsonify, request

from exceptions import NotFoundError
from models import produto_model
from validators import produto_validator
from views import serializers

logger = logging.getLogger(__name__)


def _buscar_ou_404(produto_id, extra=None):
    produto = produto_model.buscar_por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado", extra)
    return produto


def listar_produtos():
    produtos = produto_model.listar_todos()
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": serializers.produtos(produtos), "sucesso": True}), 200


def buscar_produto(id):
    produto = _buscar_ou_404(id, {"sucesso": False})
    return jsonify({"dados": serializers.produto(produto), "sucesso": True}), 200


def criar_produto():
    campos = produto_validator.validar_produto(request.get_json(silent=True))
    novo_id = produto_model.criar(**campos)
    logger.info("Produto criado com ID: %s", novo_id)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar_produto(id):
    dados = request.get_json(silent=True)
    _buscar_ou_404(id)
    campos = produto_validator.validar_produto(dados)
    produto_model.atualizar(id, **campos)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id):
    _buscar_ou_404(id)
    produto_model.deletar(id)
    logger.info("Produto %s deletado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    filtros = produto_validator.validar_filtros_busca(request.args)
    resultados = produto_model.buscar(**filtros)
    return jsonify({
        "dados": serializers.produtos(resultados),
        "total": len(resultados),
        "sucesso": True,
    }), 200
