"""Regra de negócio de usuários: cadastro e autenticação."""
import logging

from config.constants import TIPO_USUARIO_PADRAO
from middlewares.error_handler import AppError
from services.senha_service import hash_senha, verificar_senha

logger = logging.getLogger(__name__)


class UsuarioService:
    def __init__(self, usuario_model):
        self._usuarios = usuario_model

    def criar(self, nome, email, senha):
        return self._usuarios.criar(nome, email, hash_senha(senha), TIPO_USUARIO_PADRAO)

    def autenticar(self, email, senha):
        for row in self._usuarios.buscar_credenciais_por_email(email):
            valida, precisa_rehash = verificar_senha(senha, row["senha"])
            if valida:
                if precisa_rehash:
                    self._usuarios.atualizar_senha(row["id"], hash_senha(senha))
                logger.info("Login bem-sucedido (usuario_id=%s)", row["id"])
                return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
        logger.info("Login falhou")
        raise AppError("Email ou senha inválidos", 401, {"sucesso": False})
