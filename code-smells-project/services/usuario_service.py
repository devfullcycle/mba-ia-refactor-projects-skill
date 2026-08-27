from database import db
from models.usuario import Usuario

class UsuarioService:
    @staticmethod
    def listar_usuarios():
        usuarios = Usuario.query.all()
        return [u.to_dict() for u in usuarios]

    @staticmethod
    def buscar_usuario(id):
        usuario = Usuario.query.get(id)
        return usuario.to_dict() if usuario else None

    @staticmethod
    def criar_usuario(nome, email, senha):
        if not nome or not email or not senha:
            raise ValueError("Nome, email e senha são obrigatórios")
        
        novo_usuario = Usuario(nome=nome, email=email, senha=senha)
        db.session.add(novo_usuario)
        db.session.commit()
        return novo_usuario.id

    @staticmethod
    def login(email, senha):
        if not email or not senha:
            raise ValueError("Email e senha são obrigatórios")
        
        usuario = Usuario.query.filter_by(email=email, senha=senha).first()
        if usuario:
            return {
                "id": usuario.id,
                "nome": usuario.nome,
                "email": usuario.email,
                "tipo": usuario.tipo
            }
        return None
