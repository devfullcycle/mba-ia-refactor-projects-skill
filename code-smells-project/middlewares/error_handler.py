"""Tratamento de erro centralizado — remove o try/except duplicado de cada controller."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc):
        return jsonify({"erro": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc):
        logger.exception("Erro não tratado")
        return jsonify({"erro": str(exc)}), 500
