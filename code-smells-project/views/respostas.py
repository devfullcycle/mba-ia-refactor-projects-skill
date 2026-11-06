from flask import jsonify


def resposta(dados=None, status=200, mensagem=None, **extras):
    """Envelope padrão de sucesso: {"dados": ..., "sucesso": true, "mensagem": ...}."""
    corpo = {"sucesso": True}
    if dados is not None:
        corpo["dados"] = dados
    if mensagem:
        corpo["mensagem"] = mensagem
    corpo.update(extras)
    return jsonify(corpo), status


def resposta_erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status
