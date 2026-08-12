"""Tratamento de erros centralizado.

Substitui os try/except repetidos nos controllers por um único decorator que
converte exceções de domínio em respostas HTTP padronizadas.
"""

from functools import wraps
from flask import jsonify


class ApiError(Exception):
    """Erro de domínio com status HTTP associado."""

    def __init__(self, mensagem, status=400):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.status = status


def api_error_handler(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ApiError as exc:
            return jsonify({"erro": exc.mensagem, "sucesso": False}), exc.status
        except Exception as exc:  # noqa: BLE001 — boundary de erro
            return jsonify({"erro": str(exc), "sucesso": False}), 500

    return wrapper


def register_error_handlers(app):
    """Registra handlers globais de erro no app Flask."""

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"erro": "Rota não encontrada", "sucesso": False}), 404

    @app.errorhandler(500)
    def internal_error(_):
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500