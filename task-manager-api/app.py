import datetime
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config.settings import Config
from database import db
from views.task_routes import task_bp
from views.user_routes import user_bp
from views.category_routes import category_bp
from views.report_routes import report_bp
from middlewares.error_handler import register_error_handlers


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)
    JWTManager(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(category_bp)
    app.register_blueprint(report_bp)

    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'timestamp': str(datetime.datetime.utcnow())}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '1.0'}

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT'],
    )
