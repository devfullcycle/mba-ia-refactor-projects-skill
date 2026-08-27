from flask import Blueprint
import controllers.report_controller as report_controller
import controllers.category_controller as category_controller

report_bp = Blueprint('reports', __name__)

report_bp.route('/reports/summary', methods=['GET'])(report_controller.summary_report)
report_bp.route('/reports/user/<int:user_id>', methods=['GET'])(report_controller.user_report)

report_bp.route('/categories', methods=['GET'])(category_controller.get_categories)
report_bp.route('/categories', methods=['POST'])(category_controller.create_category)
report_bp.route('/categories/<int:cat_id>', methods=['PUT'])(category_controller.update_category)
report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])(category_controller.delete_category)
