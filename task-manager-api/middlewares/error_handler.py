import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Centraliza o tratamento de erros e exceções não tratadas da aplicação."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        response = {
            'error': error.description,
            'status_code': error.code
        }
        return jsonify(response), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        logger.error(f"Exceção não tratada capturada pelo middleware global: {str(error)}", exc_info=True)
        response = {
            'error': 'Erro interno do servidor',
            'details': str(error) if app.config.get('DEBUG') else 'Consulte os logs do servidor'
        }
        return jsonify(response), 500
