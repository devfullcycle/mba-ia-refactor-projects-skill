from flask import Blueprint, jsonify
from controllers.report_controller import ReportController

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    result, status = ReportController.summary()
    return jsonify(result), status


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    result, status = ReportController.user_report(user_id)
    return jsonify(result), status
