"""Tratamento de erros centralizado: único lugar que converte exceções em respostas HTTP."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"erro": err.message, "sucesso": False}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"erro": err.description, "sucesso": False}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(err):
        logger.exception("Erro inesperado: %s", err)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
