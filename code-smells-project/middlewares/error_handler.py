import logging
from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"erro": "Requisição inválida", "detalhes": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"erro": "Método não permitido"}), 405

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("Erro interno: %s", e)
        return jsonify({"erro": "Erro interno do servidor"}), 500
