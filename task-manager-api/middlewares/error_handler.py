"""Tratamento central de erros: formato único `{"error": "<mensagem>"}`; detalhes só no log."""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from utils.errors import AppError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(err):
        return jsonify({'error': err.message}), err.status

    @app.errorhandler(HTTPException)
    def handle_http_exception(err):
        # 404/405/415 etc. mantêm a resposta padrão do Flask (contrato original).
        return err

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        logger.exception('Erro não tratado: %s', err)
        return jsonify({'error': 'Erro interno'}), 500
