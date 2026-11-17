from flask import Blueprint

from controllers import report_controller as c

report_bp = Blueprint('reports', __name__)

report_bp.add_url_rule('/reports/summary', view_func=c.summary_report, methods=['GET'])
report_bp.add_url_rule('/reports/user/<int:user_id>', view_func=c.user_report, methods=['GET'])
