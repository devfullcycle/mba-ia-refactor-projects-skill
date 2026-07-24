"""Tratamento de erro centralizado.

Substitui os 16 blocos `except Exception as e: return jsonify({"erro": str(e)}), 500`
espalhados pelo controller legado. Detalhe interno vai para o log; o cliente recebe
mensagem controlada.
"""
from flask import jsonify
from werkzeug.exceptions import HTTPException


class AppError(Exception):
    """Erro de aplicação com status HTTP e mensagem seguros para exposição."""

    status = 500
    message = "Erro interno"

    def __init__(self, message=None, details=None):
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details


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


class BusinessRuleError(AppError):
    """Regra de negócio violada (ex.: estoque insuficiente)."""

    status = 400
    message = "Operação não permitida"


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _handle_app_error(error):
        payload = {"erro": error.message, "sucesso": False}
        if error.details:
            payload["detalhes"] = error.details
        return jsonify(payload), error.status

    @app.errorhandler(HTTPException)
    def _handle_http_exception(error):
        # Preserva o status das exceções do framework (404, 405, 415...) em JSON.
        return (
            jsonify({"erro": error.description, "sucesso": False}),
            error.code or 500,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(error):
        app.logger.exception("Erro não tratado: %s", error)
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500
