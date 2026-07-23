"""Views HTTP de relatórios e categorias."""

from flask import Blueprint, jsonify, request

from routes.auth import ALL_ROLES, MANAGEMENT_ROLES, require_roles
from routes.dependencies import get_controller
from schemas.presenters import (
    present_category,
    present_message,
    present_summary_report,
    present_user_report,
)


report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
@require_roles(*MANAGEMENT_ROLES)
def summary_report():
    report = get_controller("reports").summary()
    return jsonify(present_summary_report(report)), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@require_roles(*MANAGEMENT_ROLES)
def user_report(user_id):
    user, statistics = get_controller("reports").user(user_id)
    return jsonify(present_user_report(user, statistics)), 200


@report_bp.route("/categories", methods=["GET"])
@require_roles(*ALL_ROLES)
def get_categories():
    categories = get_controller("categories").list()
    return jsonify(
        [
            present_category(category, include_task_count=True, task_count=count)
            for category, count in categories
        ]
    ), 200


@report_bp.route("/categories", methods=["POST"])
@require_roles(*MANAGEMENT_ROLES)
def create_category():
    category = get_controller("categories").create(request.get_json(silent=True))
    return jsonify(present_category(category)), 201


@report_bp.route("/categories/<int:cat_id>", methods=["PUT"])
@require_roles(*MANAGEMENT_ROLES)
def update_category(cat_id):
    category = get_controller("categories").update(
        cat_id,
        request.get_json(silent=True),
    )
    return jsonify(present_category(category)), 200


@report_bp.route("/categories/<int:cat_id>", methods=["DELETE"])
@require_roles(*MANAGEMENT_ROLES)
def delete_category(cat_id):
    get_controller("categories").delete(cat_id)
    return jsonify(present_message("Categoria deletada")), 200
