"""Tratamento central de erros com formato uniforme: {"erro": "..."}."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from exceptions import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        if e.status >= 500:
            logger.error("Erro de aplicação: %s", e.message)
        return jsonify({"erro": e.message, **e.extra}), e.status

    @app.errorhandler(HTTPException)
    def handle_http_error(e):
        return e

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Erro inesperado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
