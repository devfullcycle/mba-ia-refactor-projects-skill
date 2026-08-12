"""Entry point / Composition root da aplicação Flask.

Registra blueprints e middlewares; não contém regra de negócio.
"""

from flask import Flask
from flask_cors import CORS

from config import settings
from routes import produtos_bp, usuarios_bp, pedidos_bp
from routes.system_routes import system_bp
from middlewares.error_handler import register_error_handlers
from database import get_db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)

    # Blueprints por domínio (rotas finas que delegam a controllers)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(system_bp)

    # Tratamento de erros centralizado
    register_error_handlers(app)

    return app


app = create_app()


if __name__ == "__main__":
    get_db()  # inicializa o schema e seed no boot
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://{settings.HOST}:{settings.PORT}")
    print("=" * 50)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)