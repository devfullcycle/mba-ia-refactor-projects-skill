from flask import current_app, jsonify

from config.settings import APP_VERSAO
from controllers import servicos
from views.respostas import resposta


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": APP_VERSAO,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health():
    contagens = servicos().sistema.contagens()
    if contagens is None:
        return jsonify({"status": "erro", "detalhes": "Banco de dados indisponível"}), 500
    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": APP_VERSAO,
        "ambiente": current_app.extensions["settings"].ambiente,
    }), 200


def resetar_banco():
    servicos().sistema.resetar_banco()
    return resposta(mensagem="Banco de dados resetado")
