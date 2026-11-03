import logging

from flask import Flask
from flask_cors import CORS

from src.config import database, seed
from src.config.settings import Config
from src.middlewares.error_handler import register_error_handlers
from src.models import usuario_model
from src.routes import register_routes


def create_app(config_class=Config):
    config_class.validar()

    app = Flask(__name__)
    app.config.from_object(config_class)
    logging.basicConfig(level=app.config["LOG_LEVEL"], format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    CORS(app)
    database.init_app(app)
    register_error_handlers(app)
    register_routes(app)

    with app.app_context():
        database.init_schema()
        if app.config["SEED_DB"]:
            seed.seed_if_empty()
        usuario_model.migrar_senhas_legadas()

    return app


def main(app=None):
    app = app or create_app()
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", app.config["HOST"], app.config["PORT"])
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
