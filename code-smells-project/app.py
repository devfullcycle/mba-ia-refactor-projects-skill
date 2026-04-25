import logging
from flask import Flask, jsonify
from flask_cors import CORS
import config.settings as settings
from database.connection import close_db
from database.schema import init_db
from routes.product_routes import bp as product_bp
from routes.user_routes import bp as user_bp
from routes.order_routes import bp as order_bp
from routes.report_routes import bp as report_bp
from routes.admin_routes import bp as admin_bp

logging.basicConfig(level=logging.INFO)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DATABASE_PATH"] = settings.DATABASE_PATH

    CORS(app)

    app.register_blueprint(product_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(admin_bp)

    app.teardown_appcontext(close_db)

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo a API da Loja",
            "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    init_db(app)

    return app


if __name__ == "__main__":
    app = create_app()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
