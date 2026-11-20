"""Composition root: wires config → DB → repositories → services → controllers → views."""
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .config.settings import load_settings
from .controllers import CategoryController, ReportController, TaskController, UserController
from .middlewares.error_handler import register_error_handlers
from .models import CategoryRepository, TaskRepository, UserRepository, db
from .services import NotificationService, TokenService
from .views import (
    build_category_blueprint,
    build_report_blueprint,
    build_system_blueprint,
    build_task_blueprint,
    build_user_blueprint,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(settings=None):
    settings = settings or load_settings()

    app = Flask(__name__, instance_path=str(PROJECT_ROOT / "instance"))
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SQLALCHEMY_DATABASE_URI=settings.database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEBUG=settings.debug,
    )
    CORS(app, origins=list(settings.cors_origins))

    db.init_app(app)
    with app.app_context():
        db.create_all()

    tasks = TaskRepository(db.session)
    users = UserRepository(db.session)
    categories = CategoryRepository(db.session)
    token_service = TokenService(settings.secret_key, settings.token_max_age)
    app.extensions["notification_service"] = NotificationService(
        settings.smtp_host, settings.smtp_port, settings.smtp_user, settings.smtp_password
    )

    app.register_blueprint(build_system_blueprint())
    app.register_blueprint(build_task_blueprint(TaskController(tasks, users, categories)))
    app.register_blueprint(build_user_blueprint(UserController(users, tasks, token_service), token_service))
    app.register_blueprint(build_category_blueprint(CategoryController(categories, tasks)))
    app.register_blueprint(build_report_blueprint(ReportController(tasks, users, categories)))
    register_error_handlers(app)
    return app
