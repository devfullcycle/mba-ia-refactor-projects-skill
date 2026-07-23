from flask import Blueprint, jsonify
from controllers import relatorio_controller

relatorio_bp = Blueprint("relatorios", __name__)


@relatorio_bp.route("/relatorios/vendas", methods=["GET"])
def relatorio_vendas():
    body, status = relatorio_controller.relatorio_vendas()
    return jsonify(body), status
