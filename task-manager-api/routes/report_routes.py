from flask import Blueprint, request, jsonify

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from services.report_service import ReportService

report_bp = Blueprint('reports', __name__)
reports = ReportService()


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(reports.summary()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    return jsonify(reports.user_report(user)), 200


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    result = []
    for c in Category.query.all():
        data = c.to_dict()
        data['task_count'] = Task.query.filter_by(category_id=c.id).count()
        result.append(data)
    return jsonify(result), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    data = request.get_json()
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']
    db.session.commit()
    return jsonify(cat.to_dict()), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    cat = db.session.get(Category, cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message': 'Categoria deletada'}), 200
