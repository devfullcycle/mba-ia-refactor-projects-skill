"""Rotas de Relatórios.

Passam a exigir token: os relatórios agregam dados de produtividade de todos os usuários
(nome, e-mail e desempenho) e estavam abertos a qualquer cliente.
"""
from flask import Blueprint, jsonify


def create_report_blueprint(controller, auth):
    blueprint = Blueprint("reports", __name__)
    require_auth = auth["require_auth"]

    @blueprint.route("/reports/summary", methods=["GET"])
    @require_auth
    def summary_report():
        body, status = controller.summary()
        return jsonify(body), status

    @blueprint.route("/reports/user/<int:user_id>", methods=["GET"])
    @require_auth
    def user_report(user_id):
        body, status = controller.by_user(user_id)
        return jsonify(body), status

    return blueprint
