from flask import Blueprint, jsonify

from ..controllers.relatorio_controller import RelatorioController


def build_relatorio_routes(controller: RelatorioController) -> Blueprint:
    bp = Blueprint("relatorios", __name__)

    @bp.get("/relatorios/vendas")
    def relatorio_vendas():
        return jsonify({"dados": controller.vendas(), "sucesso": True}), 200

    return bp
