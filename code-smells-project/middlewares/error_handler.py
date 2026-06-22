import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"erro": "Método não permitido", "sucesso": False}), 405

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"erro": "Requisição inválida", "sucesso": False}), 400

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        logger.exception("Erro inesperado: %s", e)
        return jsonify({"erro": "Erro interno do servidor", "sucesso": False}), 500
