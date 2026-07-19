"""Composition root — monta a aplicação, registra camadas e sobe o servidor."""
from flask import Flask
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from views.task_routes import task_bp
from views.user_routes import user_bp
from views.report_routes import report_bp
from views.category_routes import category_bp
from views.health_routes import health_bp


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app)
    db.init_app(app)

    # Garante que os models estão importados/registrados no metadata.
    import models  # noqa: F401

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(health_bp)

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
