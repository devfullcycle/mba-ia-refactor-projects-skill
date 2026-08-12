"""Rotas de relatórios e categorias — finas, delegam ao serviço."""

from flask import Blueprint, request, jsonify

from services import report_service
from middlewares.error_handler import api_error_handler

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
@api_error_handler
def summary_report():
    return jsonify(report_service.summary_report()), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@api_error_handler
def user_report(user_id):
    return jsonify(report_service.user_report(user_id)), 200


@report_bp.route("/categories", methods=["GET"])
@api_error_handler
def get_categories():
    return jsonify(report_service.list_categories()), 200


@report_bp.route("/categories", methods=["POST"])
@api_error_handler
def create_category():
    return jsonify(report_service.create_category(request.get_json())), 201


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@api_error_handler
def update_category(cat_id):
    return jsonify(report_service.update_category(cat_id, request.get_json())), 200


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@api_error_handler
def delete_category(cat_id):
    report_service.delete_category(cat_id)
    return jsonify({"message": "Categoria deletada"}), 200