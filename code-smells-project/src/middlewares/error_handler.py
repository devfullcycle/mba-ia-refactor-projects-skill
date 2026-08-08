"""Map domain errors to JSON HTTP responses."""

from __future__ import annotations

import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from src.services.errors import DomainError

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(DomainError)
    def handle_domain_error(exc: DomainError):
        payload = {"erro": exc.message, "sucesso": False}
        return jsonify(payload), exc.status_code

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        if isinstance(exc, HTTPException):
            return exc
        logger.exception("Unhandled error: %s", exc)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
