from flask import jsonify
import logging

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_error_handlers(app):

    @app.errorhandler(AppError)
    def handle_app_error(error):
        logger.warning(f"AppError: {error.message}")
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(404)
    def handle_not_found(error):
        return jsonify({'error': 'Recurso não encontrado'}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({'error': 'Método não permitido'}), 405

    @app.errorhandler(Exception)
    def handle_generic_error(error):
        logger.error(f"Unhandled error: {str(error)}", exc_info=True)
        return jsonify({'error': 'Erro interno do servidor'}), 500
