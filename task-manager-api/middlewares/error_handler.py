"""Tratamento de erro centralizado — substitui try/except repetido nas rotas."""
from flask import jsonify

from database import db


class ApiError(Exception):
    """Erro de domínio com código HTTP e mensagem já no contrato ({'error': ...})."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify({'error': err.message}), err.status_code

    @app.errorhandler(404)
    def handle_not_found(err):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # Qualquer falha não tratada volta o estado do banco e responde 500 genérico.
        db.session.rollback()
        app.logger.exception('Erro não tratado: %s', err)
        return jsonify({'error': 'Erro interno'}), 500
