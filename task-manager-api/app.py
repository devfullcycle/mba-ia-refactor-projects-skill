import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from middlewares.error_handler import register_error_handlers
from utils.helpers import now_utc


def create_app(config=Config):
    """Application factory — entry point claro e configurável."""
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config.from_object(config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok', 'timestamp': str(now_utc())})

    @app.route('/')
    def index():
        return jsonify({'message': 'Task Manager API', 'version': '1.0'})

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
