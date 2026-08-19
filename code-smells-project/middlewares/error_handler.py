from flask import jsonify
import logging

logger = logging.getLogger(__name__)

def setup_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("Erro não tratado interceptado pelo middleware de erro global")
        return jsonify({
            "sucesso": False,
            "erro": "Ocorreu um erro interno no servidor",
            "detalhes": str(e)
        }), 500
