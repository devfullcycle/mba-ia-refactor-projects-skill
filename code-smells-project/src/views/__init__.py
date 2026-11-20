from .admin_routes import build_admin_routes
from .pedido_routes import build_pedido_routes
from .produto_routes import build_produto_routes
from .relatorio_routes import build_relatorio_routes
from .sistema_routes import build_sistema_routes
from .usuario_routes import build_usuario_routes

__all__ = [
    "build_admin_routes",
    "build_pedido_routes",
    "build_produto_routes",
    "build_relatorio_routes",
    "build_sistema_routes",
    "build_usuario_routes",
]
