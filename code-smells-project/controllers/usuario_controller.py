from flask import request, jsonify


class UsuarioController:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def listar(self):
        return jsonify({"dados": self._usuarios.list(), "sucesso": True}), 200

    def buscar(self, id):
        usuario = self._usuarios.get(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404

    def criar(self):
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400
        nome = dados.get("nome", "")
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not nome or not email or not senha:
            return jsonify({"erro": "Nome, email e senha são obrigatórios"}), 400
        novo_id = self._usuarios.create(nome, email, senha)
        return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201

    def login(self):
        dados = request.get_json()
        email = dados.get("email", "")
        senha = dados.get("senha", "")
        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400
        usuario = self._usuarios.authenticate(email, senha)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
