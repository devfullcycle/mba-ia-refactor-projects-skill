import os
import logging
from datetime import datetime
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from database import db
from routes.task_routes import task_bp
from routes.user_routes import user_bp
from routes.report_routes import report_bp

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG if os.environ.get('DEBUG', 'false').lower() == 'true' else logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-only-fallback-change-in-prod')

CORS(app)
db.init_app(app)

app.register_blueprint(task_bp)
app.register_blueprint(user_bp)
app.register_blueprint(report_bp)


@app.route('/health')
def health():
    return {'status': 'ok', 'timestamp': str(datetime.utcnow())}


@app.route('/')
def index():
    return {'message': 'Task Manager API', 'version': '2.0.0'}


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=5000)
