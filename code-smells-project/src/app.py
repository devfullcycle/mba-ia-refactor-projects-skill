"""Composition root: config → DB → models → services → controllers → views."""
from typing import Optional

from flask import Flask
from flask_cors import CORS

from .config import API_VERSION, Settings, load_settings
from .controllers import (
    AdminController,
    PedidoController,
    ProdutoController,
    RelatorioController,
    SistemaController,
    UsuarioController,
)
from .middlewares import build_require_admin, register_error_handlers
from .models import AdminModel, Database, PedidoModel, ProdutoModel, RelatorioModel, UsuarioModel
from .services import NotificationService, PasswordHasher
from .views import (
    build_admin_routes,
    build_pedido_routes,
    build_produto_routes,
    build_relatorio_routes,
    build_sistema_routes,
    build_usuario_routes,
)


def create_app(settings: Optional[Settings] = None) -> Flask:
    settings = settings or load_settings()

    app = Flask(__name__)
    app.config.update(SECRET_KEY=settings.secret_key, DEBUG=settings.debug)
    CORS(app, origins=[o.strip() for o in settings.cors_origins.split(",")])

    db = Database(settings.database_path)
    app.teardown_appcontext(lambda _exc: db.close())

    hasher = PasswordHasher()
    notificacoes = NotificationService()

    db.init_schema()
    db.seed(hasher.hash)
    db.close()

    produtos = ProdutoModel(db)
    usuarios = UsuarioModel(db)
    pedidos = PedidoModel(db)

    app.register_blueprint(build_sistema_routes(
        SistemaController(produtos, usuarios, pedidos, API_VERSION, settings.environment)))
    app.register_blueprint(build_produto_routes(ProdutoController(produtos)))
    app.register_blueprint(build_usuario_routes(UsuarioController(usuarios, hasher)))
    app.register_blueprint(build_pedido_routes(PedidoController(pedidos, produtos, notificacoes)))
    app.register_blueprint(build_relatorio_routes(RelatorioController(RelatorioModel(db))))
    app.register_blueprint(build_admin_routes(
        AdminController(AdminModel(db)), build_require_admin(settings.admin_token)))

    register_error_handlers(app)
    return app
