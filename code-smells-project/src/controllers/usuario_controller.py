"""Controller de Usuário — cadastro, consulta e autenticação."""
import logging

from src.middlewares.error_handler import UnauthorizedError
from src.validators.usuario_validator import validate_login, validate_usuario

logger = logging.getLogger(__name__)


class UsuarioController:
    def __init__(self, usuario_model):
        self._model = usuario_model

    def listar(self):
        return {"dados": self._model.list_all(), "sucesso": True}, 200

    def buscar(self, usuario_id):
        usuario = self._model.get_or_fail(usuario_id)
        return {"dados": usuario, "sucesso": True}, 200

    def criar(self, dados):
        usuario = validate_usuario(dados)
        usuario_id = self._model.create(**usuario)
        logger.info("Usuário criado", extra={"usuario_id": usuario_id})
        return {"dados": {"id": usuario_id}, "sucesso": True}, 201

    def login(self, dados):
        credenciais = validate_login(dados)
        usuario = self._model.verify_credentials(**credenciais)
        if usuario is None:
            logger.warning("Tentativa de login inválida")
            raise UnauthorizedError("Email ou senha inválidos")

        logger.info("Login realizado", extra={"usuario_id": usuario["id"]})
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
