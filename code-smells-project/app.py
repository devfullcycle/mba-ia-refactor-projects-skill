import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Config
from core.db import init_app as init_db_extension, init_db
from middlewares.error_handler import register_error_handlers
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.relatorio_routes import relatorio_bp
from routes.system_routes import system_bp
from routes.usuario_routes import usuario_bp

logging.basicConfig(level=logging.INFO)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app)

    init_db_extension(app)
    register_error_handlers(app)

    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(system_bp)

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
