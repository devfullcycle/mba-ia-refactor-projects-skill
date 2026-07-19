"""Composition root — monta a aplicação: config, middlewares, rotas e conexão."""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database import close_db, init_db
from middlewares.error_handler import register_error_handlers
from views.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app)

    # Conexão com escopo por request (fecha ao fim de cada request).
    app.teardown_appcontext(close_db)

    register_error_handlers(app)
    register_routes(app)

    # Cria schema e semeia dados iniciais.
    with app.app_context():
        init_db()

    return app


logging.basicConfig(level=logging.INFO)
app = create_app()


if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:" + str(settings.PORT))
    print("=" * 50)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
