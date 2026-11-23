from flask import Blueprint

from controllers import report_controller as report_ctrl
from middlewares.auth import require_auth, require_staff

report_bp = Blueprint('reports', __name__)

report_bp.add_url_rule('/reports/summary', view_func=require_staff(report_ctrl.summary_report), methods=['GET'])
# Relatório individual: o próprio usuário ou staff (checado no controller).
report_bp.add_url_rule('/reports/user/<int:user_id>', view_func=require_auth(report_ctrl.user_report),
                       methods=['GET'])
