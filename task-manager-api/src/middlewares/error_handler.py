"""Centralized error handling — every error leaves as `{"error": <message>}`."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.controllers.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app, database):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        database.session.rollback()
        return jsonify({"error": err.message}), err.status_code

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        return jsonify({"error": err.description}), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        database.session.rollback()
        logger.exception("Erro não tratado")
        return jsonify({"error": "Erro interno do servidor"}), 500
