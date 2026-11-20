"""Centralized error handling: every error leaves the API as JSON `{"error": "..."}`."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from ..controllers.errors import AppError

logger = logging.getLogger(__name__)

HTTP_MESSAGES = {
    400: "Requisição inválida",
    404: "Recurso não encontrado",
    405: "Método não permitido",
    415: "Tipo de conteúdo não suportado",
}
MSG_INTERNAL_ERROR = "Erro interno"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"error": HTTP_MESSAGES.get(err.code, err.name)}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception("Unhandled error")
        return jsonify({"error": MSG_INTERNAL_ERROR}), 500
