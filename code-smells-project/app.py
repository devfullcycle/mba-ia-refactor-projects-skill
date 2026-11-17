import logging
from flask import Flask
from flask_cors import CORS
from config.settings import Config
from models.database import init_db
from middlewares.error_handler import register_error_handlers
from views import (
    system_bp,
    produto_bp,
    usuario_bp,
    pedido_bp,
    relatorio_bp
)

def create_app(config_class=Config):
    """Application Factory para inicialização desacoplada do Flask."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configuração de Logs
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    # Extensões e CORS
    CORS(app)

    # Inicialização do Banco de Dados
    init_db(app)

    # Registro de Middlewares e Tratamento de Erros
    register_error_handlers(app)

    # Registro de Blueprints (Camada View / Routes)
    app.register_blueprint(system_bp)
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(relatorio_bp)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
