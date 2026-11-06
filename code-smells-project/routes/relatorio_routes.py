from flask import Blueprint

from controllers import relatorio_controller as controller
from middlewares.auth import requer_autenticacao
from services.constantes import PERFIL_ADMIN

bp = Blueprint("relatorios", __name__)

bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", requer_autenticacao(PERFIL_ADMIN)(controller.vendas),
                methods=["GET"])
