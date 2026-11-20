"""HTTP layer for tasks: parse input, call the controller, serialize the response."""
from flask import Blueprint, jsonify, request

from .presenters import present_task, present_task_with_relations


def build_task_blueprint(controller):
    bp = Blueprint("tasks", __name__)

    @bp.get("/tasks")
    def list_tasks():
        return jsonify([present_task_with_relations(t) for t in controller.list_tasks()]), 200

    @bp.get("/tasks/<int:task_id>")
    def get_task(task_id):
        return jsonify(present_task(controller.get_task(task_id))), 200

    @bp.post("/tasks")
    def create_task():
        task = controller.create_task(request.get_json(silent=True))
        return jsonify(task.to_dict()), 201

    @bp.put("/tasks/<int:task_id>")
    def update_task(task_id):
        task = controller.update_task(task_id, request.get_json(silent=True))
        return jsonify(task.to_dict()), 200

    @bp.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({"message": "Task deletada com sucesso"}), 200

    @bp.get("/tasks/search")
    def search_tasks():
        args = request.args
        tasks = controller.search_tasks(
            text=args.get("q", ""),
            status=args.get("status", ""),
            priority=args.get("priority", ""),
            user_id=args.get("user_id", ""),
        )
        return jsonify([t.to_dict() for t in tasks]), 200

    @bp.get("/tasks/stats")
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
