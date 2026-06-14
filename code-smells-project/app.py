from flask import Flask, jsonify
from flask_cors import CORS
from config.settings import Config
from database import close_db, get_db
from views.product_routes import produtos_bp
from views.user_routes import usuarios_bp
from views.order_routes import pedidos_bp
from middlewares.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    app.register_blueprint(produtos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(pedidos_bp)

    app.teardown_appcontext(close_db)

    register_error_handlers(app)

    @app.route("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
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

    @app.route("/health")
    def health_check():
        try:
            db = get_db()
            db.execute("SELECT 1")
            produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
            usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
            pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
            return jsonify({
                "status": "ok",
                "database": "connected",
                "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
            }), 200
        except Exception:
            return jsonify({"status": "erro"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
