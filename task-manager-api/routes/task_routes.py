"""Rotas de tasks — finas, delegam à camada de serviço."""

from flask import Blueprint, request, jsonify

from services import task_service
from middlewares.error_handler import api_error_handler

task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
@api_error_handler
def get_tasks():
    return jsonify(task_service.list_tasks()), 200


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
@api_error_handler
def get_task(task_id):
    return jsonify(task_service.get_task(task_id)), 200


@task_bp.route("/tasks", methods=["POST"])
@api_error_handler
def create_task():
    task = task_service.create_task(request.get_json())
    return jsonify(task), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@api_error_handler
def update_task(task_id):
    task = task_service.update_task(task_id, request.get_json())
    return jsonify(task), 200


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@api_error_handler
def delete_task(task_id):
    task_service.delete_task(task_id)
    return jsonify({"message": "Task deletada com sucesso"}), 200


@task_bp.route("/tasks/search", methods=["GET"])
@api_error_handler
def search_tasks():
    result = task_service.search_tasks(
        query=request.args.get("q", ""),
        status=request.args.get("status", ""),
        priority=request.args.get("priority", ""),
        user_id=request.args.get("user_id", ""),
    )
    return jsonify(result), 200


@task_bp.route("/tasks/stats", methods=["GET"])
@api_error_handler
def task_stats():
    return jsonify(task_service.task_stats()), 200