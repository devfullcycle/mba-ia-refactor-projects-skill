from .produto_routes import produto_bp
from .usuario_routes import usuario_bp
from .pedido_routes import pedido_bp
from .relatorio_routes import relatorio_bp
from .system_routes import system_bp

__all__ = [
    "produto_bp",
    "usuario_bp",
    "pedido_bp",
    "relatorio_bp",
    "system_bp"
]
