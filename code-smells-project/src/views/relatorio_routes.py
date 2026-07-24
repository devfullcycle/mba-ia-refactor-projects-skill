"""Rotas de Relatórios."""
from flask import Blueprint, jsonify


def create_relatorio_blueprint(controller):
    blueprint = Blueprint("relatorios", __name__)

    @blueprint.route("/relatorios/vendas", methods=["GET"])
    def relatorio_vendas():
        body, status = controller.vendas()
        return jsonify(body), status

    return blueprint
