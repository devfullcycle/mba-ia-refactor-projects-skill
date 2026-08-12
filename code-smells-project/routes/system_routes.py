"""Endpoints de sistema (health check e índice) sem lógica sensível."""

from flask import Blueprint, jsonify
from config import settings


system_bp = Blueprint("system", __name__)


@system_bp.route("/health", methods=["GET"])
def health_check():
    from database import get_db

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT 1")
    cursor.execute("SELECT COUNT(*) FROM produtos")
    produtos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cursor.fetchone()[0]

    return jsonify(
        {
            "status": "ok",
            "database": "connected",
            "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            "versao": "1.0.0",
            "ambiente": "producao" if not settings.DEBUG else "desenvolvimento",
        }
    ), 200


@system_bp.route("/", methods=["GET"])
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