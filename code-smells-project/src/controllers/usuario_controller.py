import logging

from ..models.usuario_model import UsuarioModel
from ..services.password_hasher import PasswordHasher
from .errors import NotFoundError, UnauthorizedError
from .validators import validar_login, validar_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuarios: UsuarioModel, hasher: PasswordHasher):
        self.usuarios = usuarios
        self.hasher = hasher

    def listar(self) -> list:
        return self.usuarios.listar()

    def obter(self, usuario_id: int) -> dict:
        usuario = self.usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados) -> int:
        usuario = validar_usuario(dados)
        usuario_id = self.usuarios.criar(usuario["nome"], usuario["email"], self.hasher.hash(usuario["senha"]))
        logger.info("Usuário criado id=%s", usuario_id)
        return usuario_id

    def autenticar(self, dados) -> dict:
        credenciais = validar_login(dados)
        for usuario, senha_armazenada in self.usuarios.buscar_credenciais_por_email(credenciais["email"]):
            if self.hasher.verify(senha_armazenada, credenciais["senha"]):
                if not self.hasher.is_hashed(senha_armazenada):
                    self.usuarios.atualizar_senha(usuario["id"], self.hasher.hash(credenciais["senha"]))
                logger.info("Login bem-sucedido usuario_id=%s", usuario["id"])
                return {campo: usuario[campo] for campo in ("id", "nome", "email", "tipo")}
        logger.info("Falha de login")
        raise UnauthorizedError("Email ou senha inválidos")
