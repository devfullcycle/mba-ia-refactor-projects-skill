from flask import Blueprint

from controllers import task_controller as task_ctrl
from middlewares.auth import require_auth

task_bp = Blueprint('tasks', __name__)

# Leitura pública (quadro de tasks); mutações exigem login + dono ou staff (no controller).
task_bp.add_url_rule('/tasks', view_func=task_ctrl.list_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks', view_func=require_auth(task_ctrl.create_task), methods=['POST'])
task_bp.add_url_rule('/tasks/search', view_func=task_ctrl.search_tasks, methods=['GET'])
task_bp.add_url_rule('/tasks/stats', view_func=task_ctrl.task_stats, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=task_ctrl.get_task, methods=['GET'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=require_auth(task_ctrl.update_task), methods=['PUT'])
task_bp.add_url_rule('/tasks/<int:task_id>', view_func=require_auth(task_ctrl.delete_task), methods=['DELETE'])
