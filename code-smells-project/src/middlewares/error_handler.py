import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def _erro(mensagem, status):
    return jsonify({"erro": mensagem, "sucesso": False}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return _erro(exc.mensagem, exc.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return _erro(exc.description, exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc):
        # O detalhe fica só no log; o cliente recebe uma mensagem genérica.
        logger.exception("Erro não tratado")
        return _erro("Erro interno do servidor", 500)
