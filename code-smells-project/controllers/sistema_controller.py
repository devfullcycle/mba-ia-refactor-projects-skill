from flask import jsonify

from config.settings import Config


class SistemaController:
    """Endpoints de sistema: relatório, health, index e utilitário admin."""

    def __init__(self, relatorio_service, pedido_model):
        self._relatorios = relatorio_service
        self._pedidos = pedido_model

    def relatorio_vendas(self):
        return jsonify({"dados": self._relatorios.vendas(), "sucesso": True}), 200

    def health_check(self):
        counts = self._pedidos.contagens()
        # Nenhum segredo é exposto aqui (diferente da versão original).
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": counts,
            "versao": "1.0.0",
        }), 200

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def reset_db(self):
        # Utilitário destrutivo: só disponível quando explicitamente habilitado.
        if not Config.ADMIN_ENABLED:
            return jsonify({"erro": "Operação administrativa desabilitada"}), 403
        self._pedidos.reset()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
