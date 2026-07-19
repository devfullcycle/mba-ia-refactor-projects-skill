from flask import Blueprint

from controllers import task_controller
from middlewares.auth import require_auth

task_bp = Blueprint('tasks', __name__)

task_bp.add_url_rule('/tasks', 'list_tasks', task_controller.list_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/search', 'search_tasks', task_controller.search_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/stats', 'task_stats', task_controller.stats, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', 'get_task', task_controller.get_task, methods=['GET'])
task_bp.add_url_rule('/tasks', 'create_task', task_controller.create_task, methods=['POST'])
task_bp.add_url_rule('/tasks/<int:task_id>', 'update_task', task_controller.update_task, methods=['PUT'])
task_bp.add_url_rule('/tasks/<int:task_id>', 'delete_task',
                    require_auth(task_controller.delete_task), methods=['DELETE'])
