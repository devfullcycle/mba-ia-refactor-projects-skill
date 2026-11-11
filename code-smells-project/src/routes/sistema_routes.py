from flask import Blueprint, current_app, jsonify, request

from src.controllers import sistema_controller
from src.middlewares.auth import admin_token_required
from src.utils.responses import sucesso

sistema_bp = Blueprint("sistema", __name__)


@sistema_bp.get("/")
def index():
    return jsonify(sistema_controller.info_api(current_app.config["APP_VERSION"]))


@sistema_bp.get("/health")
def health_check():
    config = current_app.config
    return jsonify(sistema_controller.health_check(config["APP_VERSION"], config["APP_ENV"])), 200


@sistema_bp.post("/admin/reset-db")
@admin_token_required
def reset_database():
    sistema_controller.resetar_banco()
    return sucesso(mensagem="Banco de dados resetado")


@sistema_bp.post("/admin/query")
@admin_token_required
def executar_query():
    return sucesso(sistema_controller.executar_consulta(request.get_json(silent=True)))
