"""Usuario HTTP controllers."""

from __future__ import annotations

from flask import jsonify, request

from src.controllers.deps import usuario_service


def listar_usuarios():
    usuarios = usuario_service().listar()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(id: int):
    usuario = usuario_service().buscar_por_id(id)
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar_usuario():
    usuario_id = usuario_service().criar(request.get_json(silent=True))
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login():
    usuario = usuario_service().login(request.get_json(silent=True))
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
