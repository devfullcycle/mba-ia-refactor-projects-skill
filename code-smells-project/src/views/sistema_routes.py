from flask import Blueprint, jsonify

from ..controllers.sistema_controller import SistemaController


def build_sistema_routes(controller: SistemaController) -> Blueprint:
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify(controller.info())

    @bp.get("/health")
    def health_check():
        return jsonify(controller.health()), 200

    return bp
