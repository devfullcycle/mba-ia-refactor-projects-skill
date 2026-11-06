from flask import Blueprint

from controllers import sistema_controller as controller
from middlewares.auth import requer_autenticacao
from services.constantes import PERFIL_ADMIN

bp = Blueprint("sistema", __name__)

bp.add_url_rule("/", "index", controller.index, methods=["GET"])
bp.add_url_rule("/health", "health_check", controller.health, methods=["GET"])
# Destrutiva: exige admin e ALLOW_DESTRUCTIVE=true. A antiga POST /admin/query foi removida (CT-01).
bp.add_url_rule("/admin/reset-db", "reset_database", requer_autenticacao(PERFIL_ADMIN)(controller.resetar_banco),
                methods=["POST"])
