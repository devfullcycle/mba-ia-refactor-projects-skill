from flask import jsonify
from utils.logger import get_logger

logger = get_logger(__name__)

def register_error_handlers(app):
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("Erro não tratado: %s", str(e))
        return jsonify({"erro": "Erro interno do servidor"}), 500

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"erro": "Método não permitido"}), 405
