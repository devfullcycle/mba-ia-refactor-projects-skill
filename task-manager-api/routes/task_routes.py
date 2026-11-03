"""Rotas HTTP de Task (camada View): apenas mapeia requisição → controller → resposta."""
from flask import Blueprint, jsonify, request


def create_task_routes(controller):
    bp = Blueprint("tasks", __name__)

    @bp.get("/tasks")
    def get_tasks():
        return jsonify(controller.list_tasks()), 200

    @bp.get("/tasks/<int:task_id>")
    def get_task(task_id):
        return jsonify(controller.get_task(task_id)), 200

    @bp.post("/tasks")
    def create_task():
        return jsonify(controller.create_task(request.get_json(silent=True))), 201

    @bp.put("/tasks/<int:task_id>")
    def update_task(task_id):
        return jsonify(controller.update_task(task_id, request.get_json(silent=True))), 200

    @bp.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        controller.delete_task(task_id)
        return jsonify({"message": "Task deletada com sucesso"}), 200

    @bp.get("/tasks/search")
    def search_tasks():
        return jsonify(controller.search(request.args)), 200

    @bp.get("/tasks/stats")
    def task_stats():
        return jsonify(controller.stats()), 200

    return bp
