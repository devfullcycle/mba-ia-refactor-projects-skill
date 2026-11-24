import logging
import sqlite3

from flask import jsonify, request

from config import settings
from exceptions import AppError, ValidationError
from models import sistema_model

logger = logging.getLogger(__name__)


def index():
    return jsonify({
        "mensagem": "Bem-vindo à API da Loja",
        "versao": settings.APP_VERSION,
        "endpoints": {
            "produtos": "/produtos",
            "usuarios": "/usuarios",
            "pedidos": "/pedidos",
            "login": "/login",
            "relatorios": "/relatorios/vendas",
            "health": "/health",
        },
    })


def health_check():
    try:
        counts = sistema_model.contar_registros()
    except Exception:
        logger.exception("Falha no health check")
        return jsonify({"status": "erro", "detalhes": "Erro ao acessar o banco de dados"}), 500

    return jsonify({
        "status": "ok",
        "database": "connected",
        "counts": counts,
        "versao": settings.APP_VERSION,
        "ambiente": settings.APP_ENV,
        "db_path": settings.DB_PATH,
        "debug": settings.DEBUG,
    }), 200


def reset_database():
    sistema_model.resetar_banco()
    logger.warning("Banco de dados resetado via /admin/reset-db")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query():
    dados = request.get_json(silent=True)
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query or not isinstance(query, str):
        raise ValidationError("Query não informada")

    logger.warning("Query administrativa executada: %s", query)
    try:
        resultado = sistema_model.executar_sql(query)
    except sqlite3.Error as e:
        raise AppError(str(e))

    if resultado is not None:
        return jsonify({"dados": resultado, "sucesso": True}), 200
    return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
