from flask import Blueprint, request, jsonify
from controllers.task_controller import TaskController

task_bp = Blueprint('tasks', __name__)

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    response, status_code = TaskController.get_all_tasks()
    return jsonify(response), status_code

@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    response, status_code = TaskController.get_task_by_id(task_id)
    return jsonify(response), status_code

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    response, status_code = TaskController.create_task(data)
    return jsonify(response), status_code

@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.get_json()
    response, status_code = TaskController.update_task(task_id, data)
    return jsonify(response), status_code

@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    response, status_code = TaskController.delete_task(task_id)
    return jsonify(response), status_code

@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    response, status_code = TaskController.search_tasks(
        query=query,
        status=status,
        priority=priority,
        user_id=user_id
    )
    return jsonify(response), status_code

@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    response, status_code = TaskController.get_task_stats()
    return jsonify(response), status_code
