"""Helpers to build layered services from the request DB connection."""

from __future__ import annotations

from src.db.database import get_db
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.relatorio_model import RelatorioModel
from src.models.usuario_model import UsuarioModel
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.produto_service import ProdutoService
from src.services.relatorio_service import RelatorioService
from src.services.usuario_service import UsuarioService


def produto_service() -> ProdutoService:
    return ProdutoService(ProdutoModel(get_db()))


def usuario_service() -> UsuarioService:
    return UsuarioService(UsuarioModel(get_db()))


def pedido_service() -> PedidoService:
    return PedidoService(PedidoModel(get_db()), NotificacaoService())


def relatorio_service() -> RelatorioService:
    return RelatorioService(RelatorioModel(get_db()))
