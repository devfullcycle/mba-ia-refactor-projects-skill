from flask import jsonify


class RelatorioController:
    def __init__(self, relatorio_service):
        self._service = relatorio_service

    def vendas(self):
        return jsonify({"dados": self._service.vendas(), "sucesso": True}), 200
