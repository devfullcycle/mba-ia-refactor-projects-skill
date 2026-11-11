import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.config.database import db
from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def _error(message, status):
    # Mantém o formato de erro do contrato legado: {"error": "<mensagem>"}.
    return jsonify({"error": message}), status


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(exc):
        return _error(exc.message, exc.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_error(exc):
        return _error(exc.description, exc.code)

    @app.errorhandler(Exception)
    def handle_unexpected_error(_exc):
        # Detalhe só no log; o cliente recebe mensagem genérica e a transação é desfeita.
        db.session.rollback()
        logger.exception("Erro não tratado")
        return _error("Erro interno", 500)
