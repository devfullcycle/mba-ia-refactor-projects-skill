"""Composition root: cria a aplicação, injeta dependências e registra rotas/middlewares."""
import logging
import sqlite3

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.sistema_controller import SistemaController
from src.controllers.usuario_controller import UsuarioController
from src.database import connection
from src.database.schema import init_db
from src.middlewares.error_handler import register_error_handlers
from src.models.admin_model import AdminModel
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views.pedido_routes import create_pedido_routes
from src.views.produto_routes import create_produto_routes
from src.views.sistema_routes import create_sistema_routes
from src.views.usuario_routes import create_usuario_routes


def _bootstrap_database(settings):
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        init_db(conn, with_seed=settings.SEED_DATABASE)
    finally:
        conn.close()


def create_app(settings=Settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    app = Flask(__name__)
    app.config.from_object(settings)
    CORS(app, origins=settings.CORS_ORIGINS)

    connection.init_app(app)
    _bootstrap_database(settings)

    # Models
    produto_model = ProdutoModel(connection.get_db)
    usuario_model = UsuarioModel(connection.get_db)
    pedido_model = PedidoModel(connection.get_db)

    # Services
    notification_service = NotificationService()

    # Controllers
    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model)
    pedido_controller = PedidoController(pedido_model, produto_model, notification_service, connection.transaction)
    admin_model = AdminModel(connection.transaction, connection.get_read_only_db)
    sistema_controller = SistemaController(settings, produto_model, usuario_model, pedido_model, admin_model)

    # Views
    app.register_blueprint(create_sistema_routes(sistema_controller))
    app.register_blueprint(create_produto_routes(produto_controller))
    app.register_blueprint(create_usuario_routes(usuario_controller))
    app.register_blueprint(create_pedido_routes(pedido_controller))

    register_error_handlers(app)
    return app
