from flask import Flask
from flask_cors import CORS
from config.settings import SECRET_KEY, DEBUG, DATABASE_PATH
from config.logging_config import configure_logging
from database.connection import init_app
from routes.api_routes import api_bp
from middlewares.error_handler import register_error_handlers


def create_app():
    configure_logging(debug=DEBUG)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = SECRET_KEY
    app.config["DEBUG"] = DEBUG
    app.config["DATABASE_PATH"] = DATABASE_PATH

    CORS(app)
    init_app(app)
    app.register_blueprint(api_bp)
    register_error_handlers(app)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000)
