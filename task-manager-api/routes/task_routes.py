import logging

from flask import Blueprint, request, jsonify

from services.task_service import TaskService
from services.validators import validate_task_payload

task_bp = Blueprint('tasks', __name__)
logger = logging.getLogger(__name__)
service = TaskService()


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(service.list()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = service.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    cleaned, error, status = validate_task_payload(request.get_json())
    if error:
        return jsonify({'error': error}), status
    task = service.create(cleaned)
    logger.info("Task criada: %s - %s", task.id, task.title)
    return jsonify(task.to_dict()), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = service.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    cleaned, error, status = validate_task_payload(request.get_json(), partial=True)
    if error:
        return jsonify({'error': error}), status
    service.update(task, cleaned)
    logger.info("Task atualizada: %s", task.id)
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = service.get(task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404
    service.delete(task)
    logger.info("Task deletada: %s", task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    results = service.search(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(results), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(service.stats()), 200
