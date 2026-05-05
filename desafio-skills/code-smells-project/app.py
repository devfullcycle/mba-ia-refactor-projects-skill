from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.database import init_app as init_db_app
from src.middleware.errors import register_error_handlers
from src.views.routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Settings)
    CORS(app)
    init_db_app(app)
    register_error_handlers(app)
    register_routes(app)
    return app


app = create_app()

if __name__ == "__main__":
    with app.app_context():
        from src.database import get_db

        get_db()
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", False))
