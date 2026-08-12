"""Tratamento de erros centralizado para a API de Task Manager."""

from functools import wraps
from flask import jsonify


class ApiError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def api_error_handler(func):
    """Converter exceções de serviço em respostas HTTP JSON."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiError as exc:
            return jsonify({"error": exc.message}), exc.status
        except Exception as exc:
            # Registra o erro real mas não o expõe cru ao cliente.
            import logging

            logging.getLogger("api").exception(exc)
            return jsonify({"error": "Erro interno"}), 500

    return wrapper


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Rota não encontrada"}), 404

    @app.errorhandler(500)
    def internal_error(_):
        return jsonify({"error": "Erro interno do servidor"}), 500