"""Blueprints expostos do pacote de rotas."""

from .produto_routes import produtos_bp
from .usuario_routes import usuarios_bp
from .pedido_routes import pedidos_bp

__all__ = ["produtos_bp", "usuarios_bp", "pedidos_bp"]