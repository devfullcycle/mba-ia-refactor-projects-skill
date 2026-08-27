from flask import Flask
from flask_cors import CORS
from config.settings import Config
from database import db, init_db, get_db
from routes.routes import setup_routes
from middlewares.error_handler import setup_error_handlers

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["DEBUG"] = Config.DEBUG
CORS(app)

# Initialize database
init_db(app)

# Registra tratamento centralizado de erros
setup_error_handlers(app)

# Registra todas as rotas mapeadas para os controllers
setup_routes(app)

if __name__ == "__main__":
    # Inicializa o banco de dados ao iniciar o servidor
    get_db()
    print("=" * 50)
    print("SERVIDOR INICIADO (ARQUITETURA MVC)")
    print("Rodando em http://localhost:5002")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5002, debug=Config.DEBUG)
