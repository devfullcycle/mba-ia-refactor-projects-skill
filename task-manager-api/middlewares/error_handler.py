import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        if isinstance(e, HTTPException):
            return e
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
