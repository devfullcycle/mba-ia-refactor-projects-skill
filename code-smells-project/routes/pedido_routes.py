"""Rotas do recurso Pedidos.

Cadastro de pedido exige token de sessão de um usuário ``cliente`` e só pode
ser feito em nome do próprio usuário autenticado. Mudança de status exige
nível ``admin`` (SEC-04).
"""

from flask import Blueprint

import controllers
from config import Config
from middleware.auth import require_tipos

pedidos_bp = Blueprint("pedidos", __name__)

pedidos_bp.add_url_rule(
    "/pedidos",
    "criar_pedido",
    require_tipos(Config.PERFIL_CLIENTE)(controllers.criar_pedido),
    methods=["POST"],
)
pedidos_bp.add_url_rule("/pedidos", "listar_todos_pedidos", controllers.listar_todos_pedidos, methods=["GET"])
pedidos_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_pedidos_usuario",
    controllers.listar_pedidos_usuario,
    methods=["GET"],
)
pedidos_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status_pedido",
    require_tipos(Config.PERFIL_ADMIN)(controllers.atualizar_status_pedido),
    methods=["PUT"],
)
