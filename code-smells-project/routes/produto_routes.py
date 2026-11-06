from flask import Blueprint

from controllers import produto_controller as controller
from middlewares.auth import requer_autenticacao
from services.constantes import PERFIL_ADMIN

bp = Blueprint("produtos", __name__)
admin = requer_autenticacao(PERFIL_ADMIN)

bp.add_url_rule("/produtos", "listar_produtos", controller.listar, methods=["GET"])
bp.add_url_rule("/produtos/busca", "buscar_produtos", controller.buscar, methods=["GET"])
bp.add_url_rule("/produtos/<int:produto_id>", "buscar_produto", controller.obter, methods=["GET"])
bp.add_url_rule("/produtos", "criar_produto", admin(controller.criar), methods=["POST"])
bp.add_url_rule("/produtos/<int:produto_id>", "atualizar_produto", admin(controller.atualizar), methods=["PUT"])
bp.add_url_rule("/produtos/<int:produto_id>", "deletar_produto", admin(controller.remover), methods=["DELETE"])
