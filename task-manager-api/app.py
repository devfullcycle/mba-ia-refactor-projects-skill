from flask import Flask
from flask_cors import CORS
from database import db
from config.settings import Config
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp
from middlewares.error_handler import setup_error_handlers
from datetime import datetime, timezone

app = Flask(__name__)

# Carregar configurações robustas e seguras
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = Config.SECRET_KEY

CORS(app)
db.init_app(app)

# Registrar tratamento global de erros
setup_error_handlers(app)

# Registrar os blueprints de rotas mapeados para controllers
app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)

@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.now(timezone.utc))}

@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '1.0'}

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # Rodar na porta 5003 para evitar conflitos de portas ocupadas no macOS
    app.run(debug=True, host='0.0.0.0', port=5003)
