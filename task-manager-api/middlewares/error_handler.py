from flask import jsonify
from core.errors import AppError


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def _handle_app_error(error):
        app.logger.info("AppError: %s", error)
        return jsonify({"error": str(error)}), error.status

    @app.errorhandler(400)
    def _handle_400(_error):
        return jsonify({"error": "Requisicao invalida"}), 400

    @app.errorhandler(404)
    def _handle_404(_error):
        return jsonify({"error": "Recurso nao encontrado"}), 404

    @app.errorhandler(500)
    def _handle_500(error):
        app.logger.exception("Unhandled error: %s", error)
        return jsonify({"error": "Erro interno do servidor"}), 500

    @app.errorhandler(Exception)
    def _handle_unexpected(error):
        app.logger.exception("Unhandled exception")
        return jsonify({"error": "Erro interno do servidor"}), 500
