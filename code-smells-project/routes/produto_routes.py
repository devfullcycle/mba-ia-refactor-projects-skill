"""Rotas do recurso Produtos — apenas registro URL → handler.

Leitura é pública; escrita exige token de sessão de um usuário ``admin``
(SEC-04).
"""

from flask import Blueprint

import controllers
from config import Config
from middleware.auth import require_tipos

produtos_bp = Blueprint("produtos", __name__)

produtos_bp.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/busca", "buscar_produtos", controllers.buscar_produtos, methods=["GET"])
produtos_bp.add_url_rule("/produtos/<int:id>", "buscar_produto", controllers.buscar_produto, methods=["GET"])
produtos_bp.add_url_rule(
    "/produtos",
    "criar_produto",
    require_tipos(Config.PERFIL_ADMIN)(controllers.criar_produto),
    methods=["POST"],
)
produtos_bp.add_url_rule(
    "/produtos/<int:id>",
    "atualizar_produto",
    require_tipos(Config.PERFIL_ADMIN)(controllers.atualizar_produto),
    methods=["PUT"],
)
produtos_bp.add_url_rule(
    "/produtos/<int:id>",
    "deletar_produto",
    require_tipos(Config.PERFIL_ADMIN)(controllers.deletar_produto),
    methods=["DELETE"],
)
