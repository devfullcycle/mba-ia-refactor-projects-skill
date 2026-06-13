from flask import Flask, current_app, jsonify
from flask_cors import CORS

from config import load_settings
from database import close_db, initialize_database
from errors import AppError
import controllers


def create_app(test_config=None):
    app = Flask(__name__)
    settings = load_settings(test_config)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        DATABASE=settings.database_path,
        ADMIN_API_TOKEN=settings.admin_api_token,
    )
    if test_config:
        app.config.update(test_config)
    CORS(app)

    app.teardown_appcontext(close_db)

    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify({"erro": error.message, "sucesso": False}), error.status_code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        current_app.logger.exception("Unhandled application error")
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500

    app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/busca", "buscar_produtos", controllers.buscar_produtos, methods=["GET"])
    app.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
    app.add_url_rule("/produtos", "criar_produto", controllers.criar_produto, methods=["POST"])
    app.add_url_rule("/produtos/<int:id>", "atualizar_produto", controllers.atualizar_produto, methods=["PUT"])
    app.add_url_rule("/produtos/<int:id>", "deletar_produto", controllers.deletar_produto, methods=["DELETE"])

    app.add_url_rule("/usuarios", "listar_usuarios", controllers.listar_usuarios, methods=["GET"])
    app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", controllers.buscar_usuario, methods=["GET"])
    app.add_url_rule("/usuarios", "criar_usuario", controllers.criar_usuario, methods=["POST"])
    app.add_url_rule("/login", "login", controllers.login, methods=["POST"])

    app.add_url_rule("/pedidos", "criar_pedido", controllers.criar_pedido, methods=["POST"])
    app.add_url_rule("/pedidos", "listar_todos_pedidos", controllers.listar_todos_pedidos, methods=["GET"])
    app.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", controllers.listar_pedidos_usuario, methods=["GET"])
    app.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", controllers.atualizar_status_pedido, methods=["PUT"])

    app.add_url_rule("/relatorios/vendas", "relatorio_vendas", controllers.relatorio_vendas, methods=["GET"])
    app.add_url_rule("/health", "health_check", controllers.health_check, methods=["GET"])
    app.add_url_rule("/admin/reset-db", "reset_database", controllers.reset_database, methods=["POST"])
    app.add_url_rule("/admin/query", "executar_query", controllers.executar_query, methods=["POST"])

    @app.route("/")
    def index():
        return jsonify(
            {
                "mensagem": "Bem-vindo a API da Loja",
                "versao": "1.0.0",
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                    "admin_reset": "/admin/reset-db",
                    "admin_query": "/admin/query",
                },
            }
        )

    with app.app_context():
        initialize_database(app.config["DATABASE"])

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
