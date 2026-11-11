import logging

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


def info_api(versao):
    return {
        "mensagem": "Bem-vindo à API da Loja",
        "versao": versao,
        "endpoints": ENDPOINTS,
    }


def health_check(versao, ambiente):
    return {
        "status": "ok",
        "database": "connected",
        "counts": sistema_model.contar_registros(),
        "versao": versao,
        "ambiente": ambiente,
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
    except sistema_model.ConsultaInvalidaError:
        logger.exception("Consulta administrativa recusada")
        raise ValidationError("Consulta SQL inválida ou não permitida")
