from flask import Blueprint
import controllers.task_controller as task_controller

task_bp = Blueprint('tasks', __name__)

task_bp.route('/tasks', methods=['GET'])(task_controller.get_tasks)
task_bp.route('/tasks/<int:task_id>', methods=['GET'])(task_controller.get_task)
task_bp.route('/tasks', methods=['POST'])(task_controller.create_task)
task_bp.route('/tasks/<int:task_id>', methods=['PUT'])(task_controller.update_task)
task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])(task_controller.delete_task)
