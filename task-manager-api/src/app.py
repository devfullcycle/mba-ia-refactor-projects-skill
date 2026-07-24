"""Composition root: application factory.

O legado configurava a app, registrava blueprints, declarava rotas inline e executava
`db.create_all()` em tempo de import — o que criava o banco só por importar o módulo.
"""
from flask import Flask
from flask_cors import CORS

from src.config.logging_config import configure_logging
from src.config.settings import Config
from src.controllers.category_controller import CategoryController
from src.controllers.report_controller import HealthController, ReportController
from src.controllers.task_controller import TaskController
from src.controllers.user_controller import UserController
from src.extensions import db
from src.middlewares.auth import create_auth_middleware
from src.middlewares.error_handler import register_error_handlers
from src.models.user import User
from src.services.notification_service import build_notification_service
from src.services.token_service import TokenService
from src.views.category_routes import create_category_blueprint
from src.views.health_routes import create_health_blueprint
from src.views.report_routes import create_report_blueprint
from src.views.task_routes import create_task_blueprint
from src.views.user_routes import create_user_blueprint


def create_app(config=None, init_db=True):
    config = config or Config()

    app = Flask(__name__)
    app.config.update(config.as_flask_config())

    configure_logging(app, config.LOG_LEVEL)
    if config.SECRET_KEY_IS_EPHEMERAL:
        app.logger.warning(
            "SECRET_KEY não definida no ambiente — usando chave efêmera de "
            "desenvolvimento. Os tokens emitidos deixam de valer a cada restart."
        )

    CORS(app, origins=config.CORS_ORIGINS)
    db.init_app(app)
    register_error_handlers(app)

    # Serviços
    token_service = TokenService(config.SECRET_KEY, config.TOKEN_TTL_SECONDS)
    notification_service = build_notification_service(config.SMTP)
    auth = create_auth_middleware(token_service, User.get)

    # Controllers
    task_controller = TaskController(notification_service)
    user_controller = UserController(token_service, config.PASSWORD_MIN_LENGTH)
    category_controller = CategoryController()
    report_controller = ReportController()
    health_controller = HealthController(config.APP_VERSION)

    # Views
    app.register_blueprint(create_task_blueprint(task_controller))
    app.register_blueprint(create_user_blueprint(user_controller, auth))
    app.register_blueprint(create_category_blueprint(category_controller))
    app.register_blueprint(create_report_blueprint(report_controller, auth))
    app.register_blueprint(create_health_blueprint(health_controller))

    if init_db:
        init_database(app)

    return app


def init_database(app):
    """Criação do schema explícita — nunca como efeito colateral de import."""
    with app.app_context():
        db.create_all()
