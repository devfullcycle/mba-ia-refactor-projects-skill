"""Fluxo da aplicação para o domínio de usuários e autenticação."""

from flask import jsonify, request
from services import usuario_service
from middlewares.error_handler import api_error_handler


@api_error_handler
def listar_usuarios():
    usuarios = usuario_service.listar()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


@api_error_handler
def buscar_usuario(usuario_id):
    usuario = usuario_service.obter(usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuário não encontrado", "sucesso": False}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


@api_error_handler
def criar_usuario():
    dados = request.get_json()
    novo_id = usuario_service.criar(dados)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


@api_error_handler
def login():
    dados = request.get_json()
    usuario = usuario_service.autenticar(dados)
    if not usuario:
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200