"""Composition root: config -> DB -> repositories -> services -> controllers -> routes."""
import logging
import os

from flask import Flask
from flask_cors import CORS

from src.config.settings import load_settings
from src.controllers.category_controller import CategoryController
from src.controllers.report_controller import ReportController
from src.controllers.task_controller import TaskController
from src.controllers.user_controller import UserController
from src.middlewares.auth import Guards
from src.middlewares.error_handler import register_error_handlers
from src.models import CategoryRepository, TaskRepository, UserRepository
from src.models.database import db
from src.services.notification_service import NotificationService
from src.services.token_service import TokenService
from src.views.category_routes import build_category_routes
from src.views.report_routes import build_report_routes
from src.views.system_routes import build_system_routes
from src.views.task_routes import build_task_routes
from src.views.user_routes import build_user_routes

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(settings=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = settings or load_settings()

    app = Flask(__name__, instance_path=os.path.join(PROJECT_ROOT, "instance"))
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    CORS(app, origins=settings.cors_origins)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    tasks, users, categories = TaskRepository(db), UserRepository(db), CategoryRepository(db)
    tokens = TokenService(settings.secret_key, settings.token_max_age)
    notifications = NotificationService(
        settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password
    )
    guards = Guards(tokens, users)

    app.register_blueprint(build_system_routes())
    app.register_blueprint(build_task_routes(TaskController(tasks, users, categories)))
    app.register_blueprint(build_user_routes(UserController(users, tasks, tokens), guards))
    app.register_blueprint(build_report_routes(ReportController(tasks, users, categories)))
    app.register_blueprint(build_category_routes(CategoryController(categories, tasks)))
    register_error_handlers(app, db)

    app.extensions["settings"] = settings
    app.extensions["notification_service"] = notifications
    return app
