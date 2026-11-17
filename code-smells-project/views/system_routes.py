from flask import Blueprint, jsonify, request
from controllers.health_controller import HealthController
from models.database import get_db

system_bp = Blueprint("system", __name__)

system_bp.route("/", methods=["GET"])(HealthController.index)
system_bp.route("/health", methods=["GET"])(HealthController.health_check)

@system_bp.route("/admin/reset-db", methods=["POST"])
def reset_database():
    """Reseta dados de desenvolvimento de forma controlada."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado com sucesso", "sucesso": True}), 200

@system_bp.route("/admin/query", methods=["POST"])
def query_bloqueada():
    """Endpoint desativado por motivos de segurança (SEC-001 mitigado)."""
    return jsonify({
        "erro": "Execução arbitrária de queries SQL desativada por motivos de segurança.",
        "sucesso": False
    }), 403
