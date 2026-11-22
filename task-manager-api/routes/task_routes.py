from flask import Blueprint, jsonify, request

from controllers import task_controller
from middlewares.auth import require_auth

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_controller.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    return jsonify(task_controller.create_task(request.get_json())), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    return jsonify(task_controller.update_task(task_id, request.get_json())), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    return jsonify(task_controller.delete_task(task_id)), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    return jsonify(task_controller.search_tasks(request.args)), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_controller.task_stats()), 200
