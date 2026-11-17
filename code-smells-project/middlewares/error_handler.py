import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Centraliza o tratamento de exceções e erros HTTP na aplicação."""

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            "erro": error.description,
            "codigo": error.code,
            "sucesso": False
        }), error.code

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        logger.warning(f"Erro de validação: {str(error)}")
        return jsonify({
            "erro": str(error),
            "sucesso": False
        }), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        logger.exception("Exceção não tratada capturada pelo middleware global: %s", error)
        return jsonify({
            "erro": "Ocorreu um erro interno no servidor",
            "tipo": error.__class__.__name__,
            "sucesso": False
        }), 500
