"""Tratamento de erro centralizado.

Substitui os 12 `except:` nus do legado, que descartavam o stacktrace e devolviam 500
genérico sem registrar a causa.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    status = 500
    message = "Erro interno"

    def __init__(self, message=None):
        super().__init__(message or self.message)
        self.message = message or self.message


class ValidationError(AppError):
    status = 400
    message = "Dados inválidos"


class UnauthorizedError(AppError):
    status = 401
    message = "Credenciais inválidas"


class ForbiddenError(AppError):
    status = 403
    message = "Acesso negado"


class NotFoundError(AppError):
    status = 404
    message = "Recurso não encontrado"


class ConflictError(AppError):
    status = 409
    message = "Conflito de estado"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _handle_app_error(error):
        return jsonify({"error": error.message}), error.status

    @app.errorhandler(HTTPException)
    def _handle_http_exception(error):
        return jsonify({"error": error.description}), error.code or 500

    @app.errorhandler(Exception)
    def _handle_unexpected(error):
        # O stacktrace vai para o log; o cliente recebe mensagem genérica.
        app.logger.exception("Erro não tratado: %s", error)
        return jsonify({"error": "Erro interno"}), 500
