"""Fluxo dos casos de uso de Usuário e autenticação."""
import logging

from src.utils.errors import NotFoundError, UnauthorizedError
from src.validators.usuario_validator import validar_login, validar_novo_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def listar(self):
        return self._usuarios.listar()

    def obter(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if not usuario:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def criar(self, dados):
        usuario = validar_novo_usuario(dados)
        usuario_id = self._usuarios.criar(**usuario)
        logger.info("Usuário criado: id=%s", usuario_id)
        return usuario_id

    def login(self, dados):
        email, senha = validar_login(dados)
        usuario = self._usuarios.autenticar(email, senha)
        if not usuario:
            logger.info("Falha de login")
            raise UnauthorizedError("Email ou senha inválidos")
        logger.info("Login bem-sucedido: id=%s", usuario["id"])
        return usuario
