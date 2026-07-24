"""Rotas de Tarefa — apenas mapeamento caminho → controller."""
from flask import Blueprint, jsonify, request


def create_task_blueprint(controller):
    blueprint = Blueprint("tasks", __name__)

    @blueprint.route("/tasks", methods=["GET"])
    def get_tasks():
        body, status = controller.list()
        return jsonify(body), status

    @blueprint.route("/tasks/search", methods=["GET"])
    def search_tasks():
        body, status = controller.search(request.args)
        return jsonify(body), status

    @blueprint.route("/tasks/stats", methods=["GET"])
    def task_stats():
        body, status = controller.stats()
        return jsonify(body), status

    @blueprint.route("/tasks/<int:task_id>", methods=["GET"])
    def get_task(task_id):
        body, status = controller.get(task_id)
        return jsonify(body), status

    @blueprint.route("/tasks", methods=["POST"])
    def create_task():
        body, status = controller.create(request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/tasks/<int:task_id>", methods=["PUT"])
    def update_task(task_id):
        body, status = controller.update(task_id, request.get_json(silent=True))
        return jsonify(body), status

    @blueprint.route("/tasks/<int:task_id>", methods=["DELETE"])
    def delete_task(task_id):
        body, status = controller.delete(task_id)
        return jsonify(body), status

    return blueprint
