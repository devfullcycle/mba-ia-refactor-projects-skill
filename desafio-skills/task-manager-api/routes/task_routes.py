from flask import Blueprint, jsonify, request

from controllers import task_controller

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
def get_tasks():
    try:
        data, code = task_controller.list_tasks()
        return jsonify(data), code
    except Exception as e:
        return jsonify({"error": "Erro interno", "detail": str(e)}), 500


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    data, code = task_controller.get_task(task_id)
    return jsonify(data), code


@task_bp.route("/tasks", methods=["POST"])
def create_task():
    data, code = task_controller.create_task(request.get_json())
    return jsonify(data), code


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data, code = task_controller.update_task(task_id, request.get_json())
    return jsonify(data), code


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    data, code = task_controller.delete_task(task_id)
    return jsonify(data), code


@task_bp.route("/tasks/search", methods=["GET"])
def search_tasks():
    data, code = task_controller.search_tasks(
        request.args.get("q", ""),
        request.args.get("status", ""),
        request.args.get("priority", ""),
        request.args.get("user_id", ""),
    )
    return jsonify(data), code


@task_bp.route("/tasks/stats", methods=["GET"])
def task_stats():
    data, code = task_controller.task_stats()
    return jsonify(data), code
