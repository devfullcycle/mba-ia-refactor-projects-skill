"""Views HTTP de tasks: transporte e apresentação, sem acesso a dados."""

from flask import Blueprint, jsonify, request

from routes.auth import ALL_ROLES, MANAGEMENT_ROLES, require_roles
from routes.dependencies import get_controller
from schemas.presenters import (
    present_message,
    present_task,
    present_task_overdue,
    present_task_stats,
    present_task_with_relations,
    present_tasks,
)


task_bp = Blueprint("tasks", __name__)


@task_bp.route("/tasks", methods=["GET"])
@require_roles(*ALL_ROLES)
def get_tasks():
    tasks = get_controller("tasks").list()
    return jsonify([present_task_with_relations(task) for task in tasks]), 200


@task_bp.route("/tasks/<int:task_id>", methods=["GET"])
@require_roles(*ALL_ROLES)
def get_task(task_id):
    task = get_controller("tasks").get(task_id)
    return jsonify(present_task_overdue(task)), 200


@task_bp.route("/tasks", methods=["POST"])
@require_roles(*MANAGEMENT_ROLES)
def create_task():
    task = get_controller("tasks").create(request.get_json(silent=True))
    return jsonify(present_task(task)), 201


@task_bp.route("/tasks/<int:task_id>", methods=["PUT"])
@require_roles(*MANAGEMENT_ROLES)
def update_task(task_id):
    task = get_controller("tasks").update(
        task_id,
        request.get_json(silent=True),
    )
    return jsonify(present_task(task)), 200


@task_bp.route("/tasks/<int:task_id>", methods=["DELETE"])
@require_roles(*MANAGEMENT_ROLES)
def delete_task(task_id):
    get_controller("tasks").delete(task_id)
    return jsonify(present_message("Task deletada com sucesso")), 200


@task_bp.route("/tasks/search", methods=["GET"])
@require_roles(*ALL_ROLES)
def search_tasks():
    tasks = get_controller("tasks").search(request.args.to_dict())
    return jsonify(present_tasks(tasks)), 200


@task_bp.route("/tasks/stats", methods=["GET"])
@require_roles(*ALL_ROLES)
def task_stats():
    return jsonify(present_task_stats(get_controller("tasks").stats())), 200
