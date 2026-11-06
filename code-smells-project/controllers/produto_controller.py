import logging

from flask import request

from controllers import servicos
from controllers.validacao import validar_filtros_busca, validar_produto
from views.respostas import resposta
from views.serializers import produto_publico

logger = logging.getLogger("app.produtos")


def listar():
    produtos = servicos().produtos.listar()
    return resposta([produto_publico(p) for p in produtos])


def buscar():
    filtros = validar_filtros_busca(request.args)
    resultados = servicos().produtos.buscar(**filtros)
    return resposta([produto_publico(p) for p in resultados], total=len(resultados))


def obter(produto_id):
    return resposta(produto_publico(servicos().produtos.obter(produto_id)))


def criar():
    dados = validar_produto(request.get_json(silent=True))
    produto_id = servicos().produtos.criar(dados)
    logger.info("Produto criado: id=%s", produto_id)
    return resposta({"id": produto_id}, status=201, mensagem="Produto criado")


def atualizar(produto_id):
    # Existência antes da validação, como no contrato original (404 tem precedência sobre 400).
    servicos().produtos.obter(produto_id)
    dados = validar_produto(request.get_json(silent=True))
    servicos().produtos.atualizar(produto_id, dados)
    return resposta(mensagem="Produto atualizado")


def remover(produto_id):
    servicos().produtos.remover(produto_id)
    logger.info("Produto removido: id=%s", produto_id)
    return resposta(mensagem="Produto deletado")
