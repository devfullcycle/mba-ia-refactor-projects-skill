from flask import Blueprint, jsonify, request

from ..controllers.admin_controller import AdminController


def build_admin_routes(controller: AdminController, require_admin) -> Blueprint:
    bp = Blueprint("admin", __name__)

    @bp.post("/admin/reset-db")
    @require_admin
    def reset_database():
        controller.resetar_banco()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @bp.post("/admin/query")
    @require_admin
    def executar_query():
        dados = controller.consultar(request.get_json(silent=True))
        return jsonify({"dados": dados, "sucesso": True}), 200

    return bp
