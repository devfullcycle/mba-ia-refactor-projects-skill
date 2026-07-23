"""Single translation point from application errors to HTTP responses."""

from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from store.domain.errors import (
    ApplicationError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DeprecatedOperationError,
    IntegrityError,
    NotFoundError,
    ValidationError,
)


ERROR_STATUS = {
    ValidationError: 400,
    AuthenticationError: 401,
    AuthorizationError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    IntegrityError: 409,
    DeprecatedOperationError: 410,
}


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApplicationError)
    def handle_application_error(error: ApplicationError):
        status = next((code for error_type, code in ERROR_STATUS.items() if isinstance(error, error_type)), 400)
        return jsonify({"erro": str(error), "sucesso": False}), status

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        return jsonify({"erro": error.description, "sucesso": False}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Falha não tratada na requisição", exc_info=error)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
