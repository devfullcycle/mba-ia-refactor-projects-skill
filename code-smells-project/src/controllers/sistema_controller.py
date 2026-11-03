"""Fluxos de sistema: índice, health check e operações administrativas."""
import logging
import sqlite3

from src.utils.errors import ValidationError

logger = logging.getLogger(__name__)

ENDPOINTS_PUBLICOS = {
    "produtos": "/produtos",
    "usuarios": "/usuarios",
    "pedidos": "/pedidos",
    "login": "/login",
    "relatorios": "/relatorios/vendas",
    "health": "/health",
}


class SistemaController:
    def __init__(self, settings, produto_model, usuario_model, pedido_model, admin_model):
        self._settings = settings
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model
        self._admin = admin_model

    def indice(self):
        return {
            "mensagem": f"Bem-vindo à {self._settings.APP_NAME}",
            "versao": self._settings.APP_VERSION,
            "endpoints": ENDPOINTS_PUBLICOS,
        }

    def health(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": self._settings.APP_VERSION,
            "ambiente": self._settings.APP_ENV,
        }

    def resetar_banco(self):
        self._admin.resetar_dados()
        logger.warning("Banco de dados resetado via endpoint administrativo")

    def consultar(self, dados):
        sql = dados.get("sql", "") if isinstance(dados, dict) else ""
        if not sql or not isinstance(sql, str):
            raise ValidationError("Query não informada")
        if not sql.lstrip().upper().startswith("SELECT"):
            raise ValidationError("Apenas consultas SELECT são permitidas")
        try:
            return self._admin.consultar_somente_leitura(sql)
        except (sqlite3.Error, sqlite3.Warning) as exc:
            logger.info("Consulta administrativa rejeitada: %s", exc)
            raise ValidationError("Consulta inválida")
