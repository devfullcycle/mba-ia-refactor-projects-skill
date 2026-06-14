from flask import Blueprint, request, jsonify
from controllers.task_controller import TaskController
from middlewares.auth import login_required

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result, status = TaskController.get_all(page=page, per_page=per_page)
    return jsonify(result), status


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    result, status = TaskController.search(
        q=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(result), status


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    result, status = TaskController.get_stats()
    return jsonify(result), status


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    result, status = TaskController.get_by_id(task_id)
    return jsonify(result), status


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    result, status = TaskController.create(request.get_json() or {})
    return jsonify(result), status


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    result, status = TaskController.update(task_id, request.get_json() or {})
    return jsonify(result), status


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    result, status = TaskController.delete(task_id)
    return jsonify(result), status
