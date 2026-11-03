import logging
import sqlite3

from flask import current_app

from src.models import sistema_model
from src.utils.errors import ValidationError

logger = logging.getLogger(__name__)

ENDPOINTS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


def info_api():
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": current_app.config["APP_VERSION"],
        "endpoints": ENDPOINTS,
    }


def health_check():
    # Configurações sensíveis (secret_key, caminho do banco) não são mais expostas.
    return {
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contar_registros(),
        "versao": current_app.config["APP_VERSION"],
        "ambiente": current_app.config["APP_ENV"],
        "debug": current_app.config["DEBUG"],
    }


def resetar_banco():
    sistema_model.limpar_tabelas()
    logger.warning("Banco de dados resetado via endpoint administrativo")


def executar_consulta(dados):
    query = dados.get("sql", "") if isinstance(dados, dict) else ""
    if not query:
        raise ValidationError("Query não informada")
    if not query.strip().upper().startswith("SELECT"):
        raise ValidationError("Apenas consultas SELECT são permitidas")
    try:
        return sistema_model.executar_consulta_leitura(query)
    except sqlite3.Error:
        logger.exception("Falha ao executar consulta administrativa")
        raise ValidationError("Consulta SQL inválida")
