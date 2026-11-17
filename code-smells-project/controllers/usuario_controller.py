from flask import request, jsonify
from models.usuario_model import UsuarioModel

class UsuarioController:
    @staticmethod
    def listar_usuarios():
        usuarios = UsuarioModel.listar_todos()
        return jsonify({"dados": usuarios, "sucesso": True}), 200

    @staticmethod
    def buscar_usuario(id):
        usuario = UsuarioModel.buscar_por_id(id)
        if not usuario:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"dados": usuario, "sucesso": True}), 200

    @staticmethod
    def criar_usuario():
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        nome = str(dados.get("nome", "")).strip()
        email = str(dados.get("email", "")).strip().lower()
        senha = str(dados.get("senha", "")).strip()
        tipo = dados.get("tipo", "cliente")

        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400

        user_id = UsuarioModel.criar(nome, email, senha, tipo)
        return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201

    @staticmethod
    def login():
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        email = str(dados.get("email", "")).strip().lower()
        senha = str(dados.get("senha", "")).strip()

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = UsuarioModel.autenticar(email, senha)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
