from __future__ import annotations

from datetime import datetime

from flask import Flask
from flask_cors import CORS

from config import Settings
from controllers import (
    CategoryController,
    ReportController,
    SeedController,
    TaskController,
    UserController,
)
from database import db
from errors import register_error_handlers
from repositories import (
    CategoryRepository,
    SeedRepository,
    TaskRepository,
    UserRepository,
)
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from services.auth_service import AuthService
from services.notification_service import NotificationService


def create_app(config_overrides=None):
    settings = (
        config_overrides
        if isinstance(config_overrides, Settings)
        else Settings.load(config_overrides)
    )
    application = Flask(__name__)
    application.config.from_mapping(settings.flask_config())
    if isinstance(config_overrides, dict):
        application.config.update(config_overrides)

    if settings.cors_origins:
        CORS(application, origins=list(settings.cors_origins))
    db.init_app(application)

    auth_service = AuthService(
        settings.secret_key,
        settings.auth_token_ttl_seconds,
    )
    task_repository = TaskRepository()
    user_repository = UserRepository()
    category_repository = CategoryRepository()

    application.extensions['auth_service'] = auth_service
    application.extensions['task_manager_settings'] = settings
    application.extensions['notification_service'] = NotificationService(
        settings.smtp_host,
        settings.smtp_port,
        settings.smtp_user,
        settings.smtp_password,
        settings.smtp_timeout_seconds,
    )
    application.extensions['controllers'] = {
        'tasks': TaskController(
            task_repository,
            user_repository,
            category_repository,
            db.session,
        ),
        'users': UserController(
            user_repository,
            task_repository,
            db.session,
            auth_service,
        ),
        'categories': CategoryController(category_repository, db.session),
        'reports': ReportController(
            task_repository,
            user_repository,
            category_repository,
        ),
        'seed': SeedController(SeedRepository(), db.session),
    }

    application.register_blueprint(task_bp)
    application.register_blueprint(user_bp)
    application.register_blueprint(report_bp)
    register_error_handlers(application)

    @application.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.now())}

    @application.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    return application


if __name__ == '__main__':
    settings = Settings.load()
    app = create_app(settings)
    app.run(debug=settings.debug, host=settings.host, port=settings.port)
