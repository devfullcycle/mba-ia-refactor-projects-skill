from flask import Blueprint, request, jsonify
from controllers.report_controller import ReportController
from controllers.category_controller import CategoryController

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    response, status_code = ReportController.get_summary_report()
    return jsonify(response), status_code

@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    response, status_code = ReportController.get_user_report(user_id)
    return jsonify(response), status_code

@report_bp.route('/categories', methods=['GET'])
def get_categories():
    response, status_code = CategoryController.get_all_categories()
    return jsonify(response), status_code

@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    response, status_code = CategoryController.create_category(data)
    return jsonify(response), status_code

@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    response, status_code = CategoryController.update_category(cat_id, data)
    return jsonify(response), status_code

@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    response, status_code = CategoryController.delete_category(cat_id)
    return jsonify(response), status_code
