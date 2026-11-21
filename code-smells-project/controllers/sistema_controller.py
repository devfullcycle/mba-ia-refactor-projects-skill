"""Index, health check e operações administrativas."""
import logging

from flask import jsonify

from config.constants import APP_VERSION

logger = logging.getLogger(__name__)


class SistemaController:
    def __init__(self, manutencao_model, environment):
        self._manutencao = manutencao_model
        self._environment = environment

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": APP_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": self._manutencao.contagens(),
            "versao": APP_VERSION,
            "ambiente": self._environment,
        }), 200

    def resetar_banco(self):
        self._manutencao.resetar()
        logger.warning("Banco de dados resetado via endpoint administrativo")
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
