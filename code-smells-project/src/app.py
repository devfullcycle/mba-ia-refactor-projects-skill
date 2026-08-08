"""Flask application factory (composition root)."""

from __future__ import annotations

import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, load_settings
from src.db import database
from src.middlewares.error_handler import register_error_handlers
from src.views.routes import register_routes


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()

    logging.basicConfig(
        level=logging.DEBUG if settings.debug else logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    CORS(app)

    database.init_app(app, settings)
    register_error_handlers(app)
    register_routes(app)

    return app
