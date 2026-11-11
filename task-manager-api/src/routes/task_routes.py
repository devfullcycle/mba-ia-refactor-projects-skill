from flask import Blueprint, jsonify, request

from src.controllers import task_controller
from src.middlewares.auth import current_user, login_required
from src.utils.pagination import pagination_headers, parse_page

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
@login_required
def get_tasks():
    page = parse_page(request.args)
    tasks, total = task_controller.list_tasks(page)
    return jsonify(tasks), 200, pagination_headers(total, page)


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_task(task_id):
    return jsonify(task_controller.get_task(task_id)), 200


@task_bp.route("/tasks", methods=["POST"])
@login_required
def create_task():
    return jsonify(task_controller.create_task(request.get_json(silent=True), current_user())), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    return jsonify(task_controller.update_task(task_id, request.get_json(silent=True), current_user())), 200


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    return jsonify(task_controller.delete_task(task_id, current_user())), 200


@task_bp.route("/tasks/search", methods=["GET"])
@login_required
def search_tasks():
    page = parse_page(request.args)
    tasks, total = task_controller.search_tasks(request.args, page)
    return jsonify(tasks), 200, pagination_headers(total, page)


@task_bp.route("/tasks/stats", methods=["GET"])
@login_required
def task_stats():
    return jsonify(task_controller.task_stats()), 200
