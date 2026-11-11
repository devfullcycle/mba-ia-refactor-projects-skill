"""Envelope padrão de resposta de sucesso: {"sucesso": true, "dados": ..., "mensagem": ...}."""
from flask import jsonify


def sucesso(dados=None, status=200, mensagem=None, **extras):
    corpo = {"sucesso": True}
    if dados is not None:
        corpo["dados"] = dados
    if mensagem is not None:
        corpo["mensagem"] = mensagem
    corpo.update(extras)
    return jsonify(corpo), status
