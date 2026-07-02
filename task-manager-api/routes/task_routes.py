import logging

from flask import Blueprint, request, jsonify
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import parse_date, VALID_STATUSES
from middlewares.auth import token_required

logger = logging.getLogger(__name__)

task_bp = Blueprint('tasks', __name__)

@task_bp.route('/tasks', methods=['GET'])
@token_required
def get_tasks():
    try:
        tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
        result = [t.to_dict(include_overdue=True, include_relations=True) for t in tasks]
        return jsonify(result), 200
    except Exception as e:
        logger.exception('Erro ao listar tasks: %s', e)
        return jsonify({'error': 'Erro interno'}), 500

@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
@token_required
def get_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return jsonify(task.to_dict(include_overdue=True)), 200
    else:
        return jsonify({'error': 'Task não encontrada'}), 404

@task_bp.route('/tasks', methods=['POST'])
@token_required
def create_task():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    title = data.get('title')
    if not title:
        return jsonify({'error': 'Título é obrigatório'}), 400

    if len(title) < 3:
        return jsonify({'error': 'Título muito curto'}), 400

    if len(title) > 200:
        return jsonify({'error': 'Título muito longo'}), 400

    description = data.get('description', '')
    status = data.get('status', 'pending')
    priority = data.get('priority', 3)
    user_id = data.get('user_id')
    category_id = data.get('category_id')
    due_date = data.get('due_date')
    tags = data.get('tags')

    if status not in VALID_STATUSES:
        return jsonify({'error': 'Status inválido'}), 400

    if priority < 1 or priority > 5:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

    if user_id:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    if category_id:
        cat = Category.query.get(category_id)
        if not cat:
            return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task()
    task.title = title
    task.description = description
    task.status = status
    task.priority = priority
    task.user_id = user_id
    task.category_id = category_id

    if due_date:
        parsed = parse_date(due_date)
        if not parsed:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        task.due_date = parsed

    if tags:
        if type(tags) == list:
            task.tags = ','.join(tags)
        else:
            task.tags = tags

    try:
        db.session.add(task)
        db.session.commit()
        logger.info('Task criada: %s - %s', task.id, task.title)
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao criar task: %s', e)
        return jsonify({'error': 'Erro ao criar task'}), 500

@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'title' in data:
        if len(data['title']) < 3:
            return jsonify({'error': 'Título muito curto'}), 400
        if len(data['title']) > 200:
            return jsonify({'error': 'Título muito longo'}), 400
        task.title = data['title']

    if 'description' in data:
        task.description = data['description']

    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            return jsonify({'error': 'Status inválido'}), 400
        task.status = data['status']

    if 'priority' in data:
        if data['priority'] < 1 or data['priority'] > 5:
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
        task.priority = data['priority']

    if 'user_id' in data:
        if data['user_id']:
            user = User.query.get(data['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            cat = Category.query.get(data['category_id'])
            if not cat:
                return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    if 'due_date' in data:
        if data['due_date']:
            parsed = parse_date(data['due_date'])
            if not parsed:
                return jsonify({'error': 'Formato de data inválido'}), 400
            task.due_date = parsed
        else:
            task.due_date = None

    if 'tags' in data:
        if type(data['tags']) == list:
            task.tags = ','.join(data['tags'])
        else:
            task.tags = data['tags']

    try:
        db.session.commit()
        logger.info('Task atualizada: %s', task.id)
        return jsonify(task.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao atualizar task: %s', e)
        return jsonify({'error': 'Erro ao atualizar'}), 500

@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    try:
        db.session.delete(task)
        db.session.commit()
        logger.info('Task deletada: %s', task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        logger.exception('Erro ao deletar task: %s', e)
        return jsonify({'error': 'Erro ao deletar'}), 500

@task_bp.route('/tasks/search', methods=['GET'])
@token_required
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    results = tasks.all()
    output = [t.to_dict() for t in results]

    return jsonify(output), 200

@task_bp.route('/tasks/stats', methods=['GET'])
@token_required
def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    all_tasks = Task.query.all()
    overdue_count = sum(1 for t in all_tasks if t.is_overdue())

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
    }

    return jsonify(stats), 200
