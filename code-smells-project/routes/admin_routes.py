from flask import Blueprint, request, jsonify
from middlewares.error_handler import handle_errors, require_admin
from database.connection import get_db

bp = Blueprint("admin", __name__)


@bp.route("/admin/reset-db", methods=["POST"])
@handle_errors
@require_admin
def reset_database():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM itens_pedido")
    cursor.execute("DELETE FROM pedidos")
    cursor.execute("DELETE FROM produtos")
    cursor.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@bp.route("/admin/query", methods=["POST"])
@handle_errors
@require_admin
def executar_query():
    dados = request.get_json()
    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query nao informada"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = [dict(row) for row in rows]
            return jsonify({"dados": result, "sucesso": True}), 200
        else:
            db.commit()
            return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
