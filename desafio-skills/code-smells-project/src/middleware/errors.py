from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"erro": "Não encontrado"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"erro": "Erro interno"}), 500
