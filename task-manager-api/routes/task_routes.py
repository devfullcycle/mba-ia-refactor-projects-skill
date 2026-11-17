from flask import Blueprint

from controllers import task_controller as c
from middlewares.auth import require_auth

task_bp = Blueprint('tasks', __name__)

task_bp.add_url_rule('/tasks', view_func=c.list_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks', view_func=c.create_task, methods=['POST'])
task_bp.add_url_rule('/tasks/search', view_func=c.search_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/stats', view_func=c.task_stats, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=c.get_task, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=c.update_task, methods=['PUT'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=require_auth(c.delete_task), methods=['DELETE'])
