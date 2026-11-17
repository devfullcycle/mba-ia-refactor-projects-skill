from flask import jsonify
from models.relatorio_model import RelatorioModel

class RelatorioController:
    @staticmethod
    def relatorio_vendas():
        resumo = RelatorioModel.obter_resumo_vendas()
        return jsonify({"dados": resumo, "sucesso": True}), 200
