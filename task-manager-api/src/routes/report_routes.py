from flask import Blueprint, jsonify

from src.controllers import report_controller
from src.middlewares.auth import current_user, login_required, staff_required

report_bp = Blueprint("reports", __name__)


@report_bp.route("/reports/summary", methods=["GET"])
@staff_required
def summary_report():
    return jsonify(report_controller.summary_report()), 200


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
@login_required
def user_report(user_id):
    return jsonify(report_controller.user_report(user_id, current_user())), 200
