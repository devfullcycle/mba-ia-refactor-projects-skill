import logging
from datetime import datetime, timezone
from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('task_manager_api')

def create_app(config_class=Config):
    """Application Factory para inicialização desacoplada do Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    CORS(app)
    db.init_app(app)

    # Registrar middlewares de erro
    register_error_handlers(app)

    # Registrar Blueprints de rotas
    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health', methods=['GET'])
    def health():
        return jsonify({
            'status': 'ok',
            'timestamp': str(datetime.now(timezone.utc))
        }), 200

    @app.route('/', methods=['GET'])
    def index():
        return jsonify({
            'message': 'Task Manager API',
            'version': '1.0'
        }), 200

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    logger.info(f"Iniciando Task Manager API em http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
