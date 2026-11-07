import logging

from flask import Flask
from flask_cors import CORS

from config.settings import Config
from config.database import create_connection, init_schema
from models.produto_model import ProdutoModel
from models.usuario_model import UsuarioModel
from models.pedido_model import PedidoModel
from services.notifier import Notifier
from services.pedido_service import PedidoService
from services.relatorio_service import RelatorioService
from controllers.produto_controller import ProdutoController
from controllers.usuario_controller import UsuarioController
from controllers.pedido_controller import PedidoController
from controllers.sistema_controller import SistemaController
from views.routes import register_routes
from middlewares.error_handler import register_error_handlers


def create_app(config=Config):
    """Composition root: cria a app, injeta dependências e registra rotas."""
    logging.basicConfig(level=logging.INFO)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = config.SECRET_KEY
    app.config["DEBUG"] = config.DEBUG
    CORS(app)

    # Infraestrutura
    conn = create_connection(config.DB_PATH)
    init_schema(conn)

    # Models (recebem a conexão — sem estado global)
    produto_model = ProdutoModel(conn)
    usuario_model = UsuarioModel(conn)
    pedido_model = PedidoModel(conn)

    # Services (regra de negócio)
    notifier = Notifier()
    pedido_service = PedidoService(pedido_model, produto_model, notifier)
    relatorio_service = RelatorioService(pedido_model, config.DESCONTO_FAIXAS)

    # Controllers (fluxo HTTP)
    produto_ctrl = ProdutoController(produto_model)
    usuario_ctrl = UsuarioController(usuario_model)
    pedido_ctrl = PedidoController(pedido_service)
    sistema_ctrl = SistemaController(relatorio_service, pedido_model)

    register_routes(app, produto_ctrl, usuario_ctrl, pedido_ctrl, sistema_ctrl)
    register_error_handlers(app)
    return app


app = create_app()


if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print(f"Rodando em http://localhost:{Config.PORT}")
    print("=" * 50)
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
