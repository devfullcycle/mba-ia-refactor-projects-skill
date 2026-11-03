from flask import Blueprint, jsonify, request

from src.controllers import sistema_controller
from src.middlewares.auth import admin_token_required

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.get("/")
def index():
    return jsonify(sistema_controller.info_api())


@sistema_bp.get("/health")
def health_check():
    return jsonify(sistema_controller.health_check()), 200


@sistema_bp.post("/admin/reset-db")
@admin_token_required
def reset_database():
    sistema_controller.resetar_banco()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@sistema_bp.post("/admin/query")
@admin_token_required
def executar_query():
    dados = sistema_controller.executar_consulta(request.get_json(silent=True))
    return jsonify({"dados": dados, "sucesso": True}), 200
