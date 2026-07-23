"""Erros de aplicação e tradução central para HTTP."""

from __future__ import annotations

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db


class ApplicationError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(ApplicationError):
    status_code = 400


class UnauthorizedError(ApplicationError):
    status_code = 401


class ForbiddenError(ApplicationError):
    status_code = 403


class NotFoundError(ApplicationError):
    status_code = 404


class ConflictError(ApplicationError):
    status_code = 409


def register_error_handlers(app) -> None:
    @app.errorhandler(ApplicationError)
    def handle_application_error(error):
        db.session.rollback()
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        if isinstance(error, HTTPException):
            return error
        db.session.rollback()
        app.logger.exception("Falha não tratada durante requisição")
        return jsonify({"error": "Erro interno"}), 500
