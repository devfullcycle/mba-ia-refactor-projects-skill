from flask import Blueprint

from controllers import pedido_controller as controller
from middlewares.auth import requer_autenticacao
from services.constantes import PERFIL_ADMIN

bp = Blueprint("pedidos", __name__)
autenticado = requer_autenticacao()
admin = requer_autenticacao(PERFIL_ADMIN)

bp.add_url_rule("/pedidos", "criar_pedido", autenticado(controller.criar), methods=["POST"])
bp.add_url_rule("/pedidos", "listar_todos_pedidos", admin(controller.listar_todos), methods=["GET"])
bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                autenticado(controller.listar_do_usuario), methods=["GET"])
bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido",
                admin(controller.atualizar_status), methods=["PUT"])
