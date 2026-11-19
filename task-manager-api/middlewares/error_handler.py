import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Tratamento de erros centralizado — rotas não precisam mais de
    try/except, e detalhes internos não vazam para o cliente."""

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(400)
    def bad_request(_err):
        return jsonify({'error': 'Requisição inválida'}), 400

    @app.errorhandler(Exception)
    def internal_error(err):
        from flask import current_app
        current_app.logger.exception("Erro não tratado: %s", err)
        return jsonify({'error': 'Erro interno'}), 500
