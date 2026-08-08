"""Relatorio HTTP controllers."""

from __future__ import annotations

from flask import jsonify

from src.controllers.deps import relatorio_service


def relatorio_vendas():
    relatorio = relatorio_service().vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
