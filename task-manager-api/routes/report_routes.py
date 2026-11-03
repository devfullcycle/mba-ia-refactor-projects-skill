"""Rotas HTTP de Relatórios (camada View)."""
from flask import Blueprint, jsonify


def create_report_routes(controller):
    bp = Blueprint("reports", __name__)

    @bp.get("/reports/summary")
    def summary_report():
        return jsonify(controller.summary()), 200

    @bp.get("/reports/user/<int:user_id>")
    def user_report(user_id):
        return jsonify(controller.user_report(user_id)), 200

    return bp
