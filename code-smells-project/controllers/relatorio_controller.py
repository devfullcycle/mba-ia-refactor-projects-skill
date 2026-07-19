"""Controller de Relatórios — delega a agregação ao model."""
from flask import jsonify

from models import relatorio_model


def vendas():
    relatorio = relatorio_model.gerar()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
