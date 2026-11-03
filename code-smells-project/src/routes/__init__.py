from src.routes.pedido_routes import pedido_bp
from src.routes.produto_routes import produto_bp
from src.routes.relatorio_routes import relatorio_bp
from src.routes.sistema_routes import sistema_bp
from src.routes.usuario_routes import usuario_bp

BLUEPRINTS = (sistema_bp, produto_bp, usuario_bp, pedido_bp, relatorio_bp)


def register_routes(app):
    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)
