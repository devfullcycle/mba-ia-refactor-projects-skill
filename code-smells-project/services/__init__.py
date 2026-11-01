"""Services — regras de negócio, sem conhecimento de HTTP."""
from services import (
    admin_service,
    auth_service,
    health_service,
    notificacao_service,
    pedido_service,
    produto_service,
    usuario_service,
)

__all__ = [
    "produto_service",
    "usuario_service",
    "pedido_service",
    "notificacao_service",
    "health_service",
    "admin_service",
    "auth_service",
]
