"""Composition root: cria a aplicação, injeta dependências e registra rotas.

Nenhuma rota é declarada aqui e nenhum segredo é definido aqui — este módulo apenas monta
as camadas.
"""
from flask import Flask
from flask_cors import CORS

from src.config.logging_config import configure_logging
from src.config.settings import Config
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.usuario_controller import UsuarioController
from src.database.connection import close_connection, get_connection, init_database
from src.middlewares.error_handler import register_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notification_service import NotificationService
from src.views.health_routes import create_health_blueprint
from src.views.pedido_routes import create_pedido_blueprint
from src.views.produto_routes import create_produto_blueprint
from src.views.relatorio_routes import create_relatorio_blueprint
from src.views.usuario_routes import create_usuario_blueprint


def create_app(config=None, init_db=True):
    config = config or Config()

    app = Flask(__name__)
    app.config.update(config.as_flask_config())
    app.config["SEED_ON_INIT"] = config.SEED_ON_INIT

    configure_logging(app, config.LOG_LEVEL)
    if config.SECRET_KEY_IS_EPHEMERAL:
        app.logger.warning(
            "SECRET_KEY não definida no ambiente — usando chave efêmera de "
            "desenvolvimento. Defina SECRET_KEY antes de subir em produção."
        )

    CORS(app, origins=config.CORS_ORIGINS)
    app.teardown_appcontext(close_connection)
    register_error_handlers(app)

    # Camada de dados — a conexão é injetada como provider, não como singleton global.
    produto_model = ProdutoModel(get_connection)
    usuario_model = UsuarioModel(get_connection)
    pedido_model = PedidoModel(get_connection)

    # Serviços
    notification_service = NotificationService()

    # Controllers
    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model)
    pedido_controller = PedidoController(
        pedido_model, usuario_model, notification_service
    )
    relatorio_controller = RelatorioController(pedido_model)
    health_controller = HealthController(
        produto_model, usuario_model, pedido_model, config.APP_VERSION
    )

    # Views
    app.register_blueprint(create_produto_blueprint(produto_controller))
    app.register_blueprint(create_usuario_blueprint(usuario_controller))
    app.register_blueprint(create_pedido_blueprint(pedido_controller))
    app.register_blueprint(create_relatorio_blueprint(relatorio_controller))
    app.register_blueprint(create_health_blueprint(health_controller))

    if init_db:
        init_database(app)

    return app
