from flask import Blueprint

from controllers import report_controller

report_bp = Blueprint('reports', __name__)

report_bp.add_url_rule('/reports/summary', 'summary_report',
                      report_controller.summary_report, methods=['GET'])
report_bp.add_url_rule('/reports/user/<int:user_id>', 'user_report',
                      report_controller.user_report, methods=['GET'])
