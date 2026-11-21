"""Composition root: monta configuração, dependências, rotas e middlewares."""
import logging

from flask import Flask
from flask_cors import CORS

import database
from config import Settings, load_settings
from controllers.pedido_controller import PedidoController
from controllers.produto_controller import ProdutoController
from controllers.relatorio_controller import RelatorioController
from controllers.sistema_controller import SistemaController
from controllers.usuario_controller import UsuarioController
from middlewares.error_handler import register_error_handlers
from models.manutencao_model import ManutencaoModel
from models.pedido_model import PedidoModel
from models.produto_model import ProdutoModel
from models.usuario_model import UsuarioModel
from routes import register_routes
from services.pedido_service import PedidoService
from services.relatorio_service import RelatorioService
from services.usuario_service import UsuarioService


def create_app(settings: Settings = None) -> Flask:
    settings = settings or load_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    app.config["DATABASE_PATH"] = settings.database_path
    app.config["ADMIN_TOKEN"] = settings.admin_token
    CORS(app, origins=settings.cors_origins)

    database.init_app(app)

    produto_model = ProdutoModel(database.get_db)
    usuario_model = UsuarioModel(database.get_db)
    pedido_model = PedidoModel(database.get_db)
    manutencao_model = ManutencaoModel(database.get_db)

    controllers = {
        "produto": ProdutoController(produto_model),
        "usuario": UsuarioController(usuario_model, UsuarioService(usuario_model)),
        "pedido": PedidoController(pedido_model, PedidoService(pedido_model, produto_model)),
        "relatorio": RelatorioController(RelatorioService(pedido_model)),
        "sistema": SistemaController(manutencao_model, settings.environment),
    }
    register_routes(app, controllers)
    register_error_handlers(app)
    return app


if __name__ == "__main__":
    settings = load_settings()
    application = create_app(settings)
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    application.run(host=settings.host, port=settings.port, debug=settings.debug)
