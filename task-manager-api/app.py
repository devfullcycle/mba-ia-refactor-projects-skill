import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database import init_db
from middlewares.error_handler import register_error_handlers
from routes import register_routes


def create_app(config=None):
    """Composition root: monta config, banco, CORS, rotas e tratamento de erros."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    app = Flask(__name__)
    app.config.from_object(settings)
    if config:
        app.config.update(config)

    if app.config['SECRET_KEY'] == settings.DEV_SECRET_KEY:
        app.logger.warning('SECRET_KEY de desenvolvimento em uso; defina SECRET_KEY no ambiente.')

    CORS(app, origins=app.config['CORS_ORIGINS'])
    init_db(app)
    register_routes(app)
    register_error_handlers(app)
    return app


if __name__ == '__main__':
    create_app().run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
