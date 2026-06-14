import re
import sqlite3

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 6


class UserController:
    def __init__(self, user_model):
        self.user_model = user_model

    def list_all(self):
        return {"dados": self.user_model.find_all(), "sucesso": True}, 200

    def get_by_id(self, user_id):
        usuario = self.user_model.find_by_id(user_id)
        if not usuario:
            return {"erro": "Usuário não encontrado"}, 404
        return {"dados": usuario, "sucesso": True}, 200

    def create(self, data):
        if not data:
            return {"erro": "Dados inválidos"}, 400
        nome = data.get("nome", "").strip()
        email = data.get("email", "").strip()
        senha = data.get("senha", "")
        if not nome or not email or not senha:
            return {"erro": "Nome, email e senha são obrigatórios"}, 400
        if not EMAIL_REGEX.match(email):
            return {"erro": "Formato de email inválido"}, 400
        if len(senha) < MIN_PASSWORD_LENGTH:
            return {"erro": f"Senha deve ter pelo menos {MIN_PASSWORD_LENGTH} caracteres"}, 400
        try:
            user_id = self.user_model.create(nome, email, senha)
            return {"dados": {"id": user_id}, "sucesso": True}, 201
        except sqlite3.IntegrityError:
            return {"erro": "Email já cadastrado"}, 409
        except sqlite3.Error:
            return {"erro": "Erro de banco de dados"}, 500

    def login(self, data):
        if not data:
            return {"erro": "Dados inválidos"}, 400
        email = data.get("email", "").strip()
        senha = data.get("senha", "")
        if not email or not senha:
            return {"erro": "Email e senha são obrigatórios"}, 400
        usuario = self.user_model.authenticate(email, senha)
        if usuario:
            return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
        return {"erro": "Email ou senha inválidos", "sucesso": False}, 401
