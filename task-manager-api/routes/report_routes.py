import logging

from flask import Blueprint, request, jsonify
from sqlalchemy import func

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import timedelta
from utils.helpers import utcnow
from middlewares.auth import token_required

logger = logging.getLogger(__name__)

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports/summary', methods=['GET'])
@token_required
def summary_report():

    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    p1 = Task.query.filter_by(priority=1).count()
    p2 = Task.query.filter_by(priority=2).count()
    p3 = Task.query.filter_by(priority=3).count()
    p4 = Task.query.filter_by(priority=4).count()
    p5 = Task.query.filter_by(priority=5).count()

    all_tasks = Task.query.all()
    overdue_count = 0
    overdue_list = []
    for t in all_tasks:
        if t.is_overdue():
            overdue_count += 1
            overdue_list.append({
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (utcnow() - t.due_date).days
            })

    seven_days_ago = utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()

    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
    ).count()

    task_counts_by_user = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .group_by(Task.user_id).all()
    )
    completed_counts_by_user = dict(
        db.session.query(Task.user_id, func.count(Task.id))
        .filter(Task.status == 'done')
        .group_by(Task.user_id).all()
    )

    users = User.query.all()
    user_stats = []
    for u in users:
        total = task_counts_by_user.get(u.id, 0)
        completed = completed_counts_by_user.get(u.id, 0)
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
        })

    report = {
        'generated_at': str(utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': p1,
            'high': p2,
            'medium': p3,
            'low': p4,
            'minimal': p5,
        },
        'overdue': {
            'count': overdue_count,
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return jsonify(report), 200

@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
@token_required
def user_report(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    total = len(tasks)
    done = 0
    pending = 0
    in_progress = 0
    cancelled = 0
    overdue = 0
    high_priority = 0

    for t in tasks:
        if t.status == 'done':
            done = done + 1
        elif t.status == 'pending':
            pending = pending + 1
        elif t.status == 'in_progress':
            in_progress = in_progress + 1
        elif t.status == 'cancelled':
            cancelled = cancelled + 1

        if t.priority <= 2:
            high_priority = high_priority + 1

        if t.is_overdue():
            overdue = overdue + 1

    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
        }
    }

    return jsonify(report), 200

@report_bp.route('/categories', methods=['GET'])
@token_required
def get_categories():
    task_counts_by_category = dict(
        db.session.query(Task.category_id, func.count(Task.id))
        .group_by(Task.category_id).all()
    )

    categories = Category.query.all()
    result = []
    for c in categories:
        cat_data = c.to_dict()
        cat_data['task_count'] = task_counts_by_category.get(c.id, 0)
        result.append(cat_data)
    return jsonify(result), 200

@report_bp.route('/categories', methods=['POST'])
@token_required
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

    try:
        db.session.add(category)
        db.session.commit()
        return jsonify(category.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao criar categoria: %s', e)
        return jsonify({'error': 'Erro ao criar categoria'}), 500

@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
@token_required
def update_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    data = request.get_json()
    if 'name' in data:
        cat.name = data['name']
    if 'description' in data:
        cat.description = data['description']
    if 'color' in data:
        cat.color = data['color']

    try:
        db.session.commit()
        return jsonify(cat.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao atualizar categoria: %s', e)
        return jsonify({'error': 'Erro ao atualizar'}), 500

@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
@token_required
def delete_category(cat_id):
    cat = Category.query.get(cat_id)
    if not cat:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    try:
        db.session.delete(cat)
        db.session.commit()
        return jsonify({'message': 'Categoria deletada'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao deletar categoria: %s', e)
        return jsonify({'error': 'Erro ao deletar'}), 500
