from flask import Blueprint, jsonify
from controllers import report_controller
from middlewares.error_handler import handle_errors

bp = Blueprint("relatorios", __name__)


@bp.route("/relatorios/vendas", methods=["GET"])
@handle_errors
def relatorio_vendas():
    result, status = report_controller.sales_report()
    return jsonify(result), status


@bp.route("/health", methods=["GET"])
@handle_errors
def health_check():
    result, status = report_controller.health_check()
    return jsonify(result), status
