from flask import Flask
from flask_cors import CORS
from config import settings
from utils import database, errors, logger
from routes import register_blueprints

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.SECRET_KEY
app.config["DEBUG"] = settings.DEBUG

CORS(app, origins=settings.CORS_ORIGINS if settings.CORS_ORIGINS != ["*"] else "*")

database.init_app(app)
errors.register_error_handlers(app)
register_blueprints(app)

log = logger.get_logger(__name__)

if __name__ == "__main__":
    log.info("=" * 50)
    log.info("SERVIDOR INICIADO")
    log.info("Rodando em http://localhost:5000")
    log.info("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=settings.DEBUG)
