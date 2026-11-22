"""Composition root: carrega config, monta dependências, registra rotas e middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

import models  # noqa: F401  (registra os models no SQLAlchemy antes do create_all)
from config.settings import Settings, load_settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes import register_routes
from services.notification_service import NotificationService


def create_app(settings: Settings = None) -> Flask:
    settings = settings or load_settings()
    logging.basicConfig(
        level=settings.log_level,
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    app = Flask(__name__)
    app.config.from_mapping(settings.flask_config())
    app.extensions['settings'] = settings
    app.extensions['notification_service'] = NotificationService(
        host=settings.email_host,
        port=settings.email_port,
        user=settings.email_user,
        password=settings.email_password,
    )

    CORS(app, origins=settings.cors_origins)
    db.init_app(app)

    register_routes(app)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    config = app.extensions['settings']
    app.run(debug=config.debug, host=config.host, port=config.port)
