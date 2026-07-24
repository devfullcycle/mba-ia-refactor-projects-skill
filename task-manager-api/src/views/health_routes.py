"""Rotas de metadados e health check — eram declaradas inline no entry point."""
from flask import Blueprint, jsonify


def create_health_blueprint(controller):
    blueprint = Blueprint("health", __name__)

    @blueprint.route("/", methods=["GET"])
    def index():
        body, status = controller.index()
        return jsonify(body), status

    @blueprint.route("/health", methods=["GET"])
    def health():
        body, status = controller.health()
        return jsonify(body), status

    return blueprint
