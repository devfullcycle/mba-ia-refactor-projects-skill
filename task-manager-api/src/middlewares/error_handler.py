import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.controllers.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app, database):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        database.session.rollback()
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(error):
        if isinstance(error, HTTPException):  # keep Flask's 404/405 for unknown routes
            return error
        database.session.rollback()
        logger.exception("Unhandled error")
        return jsonify({"error": "Erro interno"}), 500
