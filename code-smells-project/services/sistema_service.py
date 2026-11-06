import logging

from database.connection import ErroBanco
from services.excecoes import AppError

logger = logging.getLogger("app.sistema")


class SistemaService:
    def __init__(self, sistema, allow_destructive):
        self._sistema = sistema
        self._allow_destructive = allow_destructive

    def contagens(self):
        """Devolve as contagens ou None se o banco estiver indisponível."""
        try:
            return self._sistema.contagens()
        except ErroBanco:
            logger.exception("Health check: falha ao acessar o banco")
            return None

    def resetar_banco(self):
        if not self._allow_destructive:
            raise AppError("Operação desabilitada (ALLOW_DESTRUCTIVE)", 403)
        self._sistema.resetar()
        logger.warning("Banco de dados resetado por administrador")
