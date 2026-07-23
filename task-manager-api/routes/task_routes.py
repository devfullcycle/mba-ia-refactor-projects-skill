from flask import Blueprint, jsonify
from controllers import task_controller

task_bp = Blueprint("tasks", __name__)


def _json(result):
    body, status = result
    return jsonify(body), status


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    return _json(task_controller.list_tasks())


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    return _json(task_controller.get_task(task_id))


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    return _json(task_controller.create_task())


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    return _json(task_controller.update_task(task_id))


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    return _json(task_controller.delete_task(task_id))


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    return _json(task_controller.search_tasks())


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    return _json(task_controller.task_stats())
