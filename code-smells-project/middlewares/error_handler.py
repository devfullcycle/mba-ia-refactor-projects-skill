"""Tratamento de erros centralizado. Detalhes internos só vão para o log."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno do servidor"


class AppError(Exception):
    """Erro de negócio/validação com status HTTP. `extra` é mesclado ao corpo da resposta."""

    def __init__(self, message, status=400, extra=None):
        super().__init__(message)
        self.message = message
        self.status = status
        self.extra = extra or {}


def _handle_app_error(error):
    return jsonify({"erro": error.message, **error.extra}), error.status


def _handle_http_error(error):
    return jsonify({"erro": error.description}), error.code


def _handle_unexpected(error):
    logger.exception("Erro inesperado: %s", error)
    return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500


def register_error_handlers(app):
    app.register_error_handler(AppError, _handle_app_error)
    app.register_error_handler(HTTPException, _handle_http_error)
    app.register_error_handler(Exception, _handle_unexpected)
