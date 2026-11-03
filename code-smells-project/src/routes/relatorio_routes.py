from flask import Blueprint, jsonify

from src.controllers import relatorio_controller

relatorio_bp = Blueprint("relatorios", __name__)


@relatorio_bp.get("/relatorios/vendas")
def relatorio_vendas():
    return jsonify({"dados": relatorio_controller.relatorio_vendas(), "sucesso": True}), 200
