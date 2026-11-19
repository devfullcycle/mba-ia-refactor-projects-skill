import logging

from flask import jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Tratamento de erros centralizado — nenhum handler precisa mais de
    try/except, e detalhes internos não vazam para o cliente."""

    @app.errorhandler(404)
    def not_found(_err):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(400)
    def bad_request(_err):
        return jsonify({"erro": "Requisição inválida"}), 400

    @app.errorhandler(Exception)
    def internal_error(err):
        logger.exception("Erro não tratado: %s", err)
        return jsonify({"erro": "Erro interno do servidor"}), 500
