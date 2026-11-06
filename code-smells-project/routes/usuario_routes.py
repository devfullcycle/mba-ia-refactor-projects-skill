from flask import Blueprint

from controllers import usuario_controller as controller
from middlewares.auth import requer_autenticacao
from services.constantes import PERFIL_ADMIN

bp = Blueprint("usuarios", __name__)

bp.add_url_rule("/usuarios", "listar_usuarios", requer_autenticacao(PERFIL_ADMIN)(controller.listar), methods=["GET"])
bp.add_url_rule("/usuarios/<int:usuario_id>", "buscar_usuario", requer_autenticacao()(controller.obter), methods=["GET"])
bp.add_url_rule("/usuarios", "criar_usuario", controller.criar, methods=["POST"])
bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
