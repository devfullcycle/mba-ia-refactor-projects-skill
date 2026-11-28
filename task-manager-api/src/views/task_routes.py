"""Task endpoints (HTTP layer only)."""
from flask import Blueprint, jsonify, request

from src.views.presenters import present_task, present_task_detail, present_task_with_relations


def build_task_routes(controller):
    bp = Blueprint("tasks", __name__)

    @bp.get("/tasks")
    def list_tasks():
        return jsonify([present_task_with_relations(task) for task in controller.list_tasks()]), 200

    @bp.get("/tasks/<int:task_id>")
    def get_task(task_id):
        return jsonify(present_task_detail(controller.get_task(task_id))), 200

    @bp.post("/tasks")
    def create_task():
        task = controller.create_task(request.get_json(silent=True))
        return jsonify(present_task(task)), 201

    @bp.put("/tasks/<int:task_id>")
    def update_task(task_id):
        task = controller.update_task(task_id, request.get_json(silent=True))
        return jsonify(present_task(task)), 200

    @bp.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({"message": "Task deletada com sucesso"}), 200

    @bp.get("/tasks/search")
    def search_tasks():
        return jsonify([present_task(task) for task in controller.search(request.args)]), 200

    @bp.get("/tasks/stats")
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
