"""Entry point e composition root: cria a app, injeta dependências e registra rotas/middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Settings
from controllers.category_controller import CategoryController
from controllers.report_controller import ReportController
from controllers.task_controller import TaskController
from controllers.user_controller import UserController
from database import db
from middlewares.error_handler import register_error_handlers
from routes.category_routes import create_category_routes
from routes.report_routes import create_report_routes
from routes.system_routes import create_system_routes
from routes.task_routes import create_task_routes
from routes.user_routes import create_user_routes
from services.notification_service import NotificationService
from services.token_service import TokenService


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)
    db.init_app(app)

    notification_service = NotificationService(settings)
    token_service = TokenService(settings.SECRET_KEY, settings.AUTH_TOKEN_MAX_AGE_SECONDS)

    app.register_blueprint(create_system_routes(settings))
    app.register_blueprint(create_task_routes(TaskController(db.session, notification_service)))
    app.register_blueprint(create_user_routes(UserController(db.session, token_service)))
    app.register_blueprint(create_report_routes(ReportController()))
    app.register_blueprint(create_category_routes(CategoryController(db.session)))
    register_error_handlers(app)

    with app.app_context():
        import models  # noqa: F401 — registra os models no metadata antes do create_all
        db.create_all()

    return app


# Instância de módulo mantida para compatibilidade (`from app import app, db` no seed.py).
app = create_app()

if __name__ == "__main__":
    app.run(host=Settings.HOST, port=Settings.PORT, debug=Settings.DEBUG)
