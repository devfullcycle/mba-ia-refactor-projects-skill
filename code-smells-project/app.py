"""Composition root: cria a app, registra rotas/middlewares e inicia o servidor."""
import logging

from flask import Flask
from flask_cors import CORS

import database
from config import settings
from middlewares.error_handler import register_error_handlers
from routes import register_routes


def create_app():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)

    database.init_db()
    database.init_app(app)
    register_routes(app)
    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    logging.getLogger(__name__).info("Rodando em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
