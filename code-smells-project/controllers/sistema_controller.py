"""Controller de sistema — index, health check e operação administrativa protegida."""
from flask import jsonify, request

from config import settings
from database import get_db


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        }
    )


def health():
    db = get_db()
    db.execute("SELECT 1")
    produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]

    return jsonify(
        {
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "versao": "1.0.0",
            "ambiente": settings.AMBIENTE,
            "db_path": settings.DB_PATH,
        }
    ), 200


def reset_database():
    """Operação destrutiva protegida por token administrativo (header X-Admin-Token)."""
    token = request.headers.get("X-Admin-Token", "")
    if not settings.ADMIN_TOKEN or token != settings.ADMIN_TOKEN:
        return jsonify({"erro": "Não autorizado"}), 403

    db = get_db()
    db.execute("DELETE FROM itens_pedido")
    db.execute("DELETE FROM pedidos")
    db.execute("DELETE FROM produtos")
    db.execute("DELETE FROM usuarios")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
