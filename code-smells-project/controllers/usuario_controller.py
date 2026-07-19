"""Controller de Usuários — valida entrada e delega autenticação/persistência ao model."""
from flask import jsonify, request

from models import usuario_model


def listar():
    usuarios = usuario_model.listar_todos()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar(id):
    usuario = usuario_model.buscar_por_id(id)
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado"}), 404


def criar():
    dados = request.get_json()

    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

    id = usuario_model.criar(nome, email, senha)
    return jsonify({"dados": {"id": id}, "sucesso": True}), 201


def login():
    dados = request.get_json()
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios"}), 400

    usuario = usuario_model.autenticar(email, senha)
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
