from flask import Blueprint, jsonify, request

from src.middlewares.auth import require_admin_token


def create_sistema_routes(controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify(controller.indice())

    @bp.get("/health")
    def health_check():
        return jsonify(controller.health()), 200

    @bp.post("/admin/reset-db")
    @require_admin_token
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @require_admin_token
    def executar_query():
        dados = controller.consultar(request.get_json(silent=True))
        return jsonify({"dados": dados, "sucesso": True}), 200

    return bp
