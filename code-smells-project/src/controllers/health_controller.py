"""Health and protected admin controllers."""

from __future__ import annotations

import logging

from flask import g, jsonify, request

from src.db.database import get_db, reset_all_data
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.errors import ForbiddenError

logger = logging.getLogger(__name__)


def health_check():
    db = get_db()
    db.execute("SELECT 1")
    settings = g._settings
    return jsonify(
        {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": ProdutoModel(db).contar(),
                "usuarios": UsuarioModel(db).contar(),
                "pedidos": PedidoModel(db).contar(),
            },
            "versao": "2.0.0",
            "ambiente": settings.ambiente,
        }
    ), 200


def index():
    return jsonify(
        {
            "mensagem": "Bem-vindo à API da Loja",
            "versao": "2.0.0",
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


def reset_database():
    settings = g._settings
    token = request.headers.get("X-Admin-Token", "")
    if not settings.admin_token or token != settings.admin_token:
        raise ForbiddenError("Admin token inválido ou não configurado")

    reset_all_data(get_db())
    logger.warning("Banco de dados resetado via admin")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
