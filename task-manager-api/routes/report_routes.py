from flask import Blueprint, jsonify
from controllers import report_controller

report_bp = Blueprint("reports", __name__)


def _json(result):
    body, status = result
    return jsonify(body), status


@report_bp.route("/reports/summary", methods=["GET"])
def summary():
    return _json(report_controller.summary())


@report_bp.route("/reports/user/<int:user_id>", methods=["GET"])
def user_report(user_id):
    return _json(report_controller.user_report(user_id))
