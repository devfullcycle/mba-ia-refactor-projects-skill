"""Controller de Usuário — cadastro, consulta, autenticação."""
import logging

from src.extensions import db
from src.middlewares.error_handler import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from src.models.task import Task
from src.models.user import User
from src.validators.user_validator import validate_login, validate_user

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, token_service, password_min_length=8):
        self._tokens = token_service
        self._password_min_length = password_min_length

    # --- consultas ---

    def list(self):
        return [
            {**usuario.to_dict(), "task_count": total}
            for usuario, total in User.list_with_task_counts()
        ], 200

    def get(self, user_id):
        usuario = self._get_or_fail(user_id)
        dados = usuario.to_dict()
        dados["tasks"] = [t.to_dict() for t in Task.list_by_user(user_id)]
        return dados, 200

    def tasks(self, user_id):
        self._get_or_fail(user_id)
        return [t.to_summary_dict() for t in Task.list_by_user(user_id)], 200

    # --- escrita ---

    def create(self, dados):
        campos = validate_user(dados, password_min_length=self._password_min_length)
        if User.email_taken(campos["email"]):
            raise ConflictError("Email já cadastrado")

        usuario = User(
            name=campos["name"], email=campos["email"], role=campos["role"]
        )
        usuario.set_password(campos["password"])

        db.session.add(usuario)
        db.session.commit()
        logger.info("Usuário criado", extra={"user_id": usuario.id})
        return usuario.to_dict(), 201

    def update(self, user_id, dados):
        usuario = self._get_or_fail(user_id)
        campos = validate_user(
            dados, partial=True, password_min_length=self._password_min_length
        )

        if "email" in campos and User.email_taken(campos["email"], exclude_id=user_id):
            raise ConflictError("Email já cadastrado")

        if "name" in campos:
            usuario.name = campos["name"]
        if "email" in campos:
            usuario.email = campos["email"]
        if "role" in campos:
            usuario.role = campos["role"]
        if "active" in campos:
            usuario.active = campos["active"]
        if "password" in campos:
            usuario.set_password(campos["password"])

        db.session.commit()
        logger.info("Usuário atualizado", extra={"user_id": user_id})
        return usuario.to_dict(), 200

    def delete(self, user_id):
        usuario = self._get_or_fail(user_id)
        # As tarefas caem por cascade do relacionamento — o legado as apagava em laço.
        db.session.delete(usuario)
        db.session.commit()
        logger.info("Usuário removido", extra={"user_id": user_id})
        return {"message": "Usuário deletado com sucesso"}, 200

    # --- autenticação ---

    def login(self, dados):
        credenciais = validate_login(dados)
        usuario = User.find_by_email(credenciais["email"])

        if usuario is None or not usuario.check_password(credenciais["password"]):
            logger.warning("Tentativa de login inválida")
            raise UnauthorizedError("Credenciais inválidas")
        if not usuario.active:
            raise ForbiddenError("Usuário inativo")

        logger.info("Login realizado", extra={"user_id": usuario.id})
        return {
            "message": "Login realizado com sucesso",
            "user": usuario.to_dict(),
            "token": self._tokens.issue(usuario),
        }, 200

    # --- apoio ---

    @staticmethod
    def _get_or_fail(user_id):
        usuario = User.get(user_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario
