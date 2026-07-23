import os
import logging
from datetime import datetime, timezone

from flask import Flask
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from routes.category_routes import category_bp

logging.basicConfig(level=logging.INFO)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)
    register_error_handlers(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(category_bp)

    @app.route("/health")
    def health():
        return {"status": "ok", "timestamp": str(datetime.now(timezone.utc))}

    @app.route("/")
    def index():
        return {"message": "Task Manager API", "version": "1.0"}

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
    )
