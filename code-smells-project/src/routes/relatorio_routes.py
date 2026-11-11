from flask import Blueprint

from src.controllers import relatorio_controller
from src.middlewares.auth import admin_required
from src.utils.responses import sucesso

relatorio_bp = Blueprint("relatorios", __name__)


@relatorio_bp.get("/relatorios/vendas")
@admin_required
def relatorio_vendas():
    return sucesso(relatorio_controller.relatorio_vendas())
