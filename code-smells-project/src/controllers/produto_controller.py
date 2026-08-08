"""Produto HTTP controllers — thin request/response adapters."""

from __future__ import annotations

from flask import jsonify, request

from src.controllers.deps import produto_service


def listar_produtos():
    produtos = produto_service().listar()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id: int):
    produto = produto_service().buscar_por_id(id)
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar_produto():
    produto_id = produto_service().criar(request.get_json(silent=True))
    return jsonify(
        {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}
    ), 201


def atualizar_produto(id: int):
    produto_service().atualizar(id, request.get_json(silent=True))
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id: int):
    produto_service().deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria") or None
    preco_min_raw = request.args.get("preco_min")
    preco_max_raw = request.args.get("preco_max")

    preco_min = float(preco_min_raw) if preco_min_raw else None
    preco_max = float(preco_max_raw) if preco_max_raw else None

    resultados = produto_service().buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
