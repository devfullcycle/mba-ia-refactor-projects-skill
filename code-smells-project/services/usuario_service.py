from models.usuario import UsuarioModel

class UsuarioService:
    @staticmethod
    def listar_usuarios():
        return UsuarioModel.get_todos()

    @staticmethod
    def buscar_usuario(id):
        return UsuarioModel.get_por_id(id)

    @staticmethod
    def criar_usuario(nome, email, senha):
        if not nome or not email or not senha:
            raise ValueError("Nome, email e senha são obrigatórios")
        return UsuarioModel.criar(nome, email, senha)

    @staticmethod
    def login(email, senha):
        if not email or not senha:
            raise ValueError("Email e senha são obrigatórios")
        return UsuarioModel.login(email, senha)
