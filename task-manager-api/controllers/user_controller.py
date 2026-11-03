"""Fluxo dos casos de uso de Usuário e autenticação."""
import logging

from models.task import Task
from models.user import User
from utils.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from validators.user_validator import validate_login, validate_new_user, validate_user_update

logger = logging.getLogger(__name__)


class UserController:
    def __init__(self, session, token_service):
        self._session = session
        self._tokens = token_service

    @staticmethod
    def _get_or_404(user_id):
        user = User.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado")
        return user

    def list_users(self):
        task_totals = Task.totals_by_user()
        return [
            {**user.to_dict(), "task_count": task_totals.get(user.id, (0, 0))[0]}
            for user in User.all()
        ]

    def get_user(self, user_id):
        user = self._get_or_404(user_id)
        return {**user.to_dict(), "tasks": [task.to_dict() for task in Task.by_user(user_id)]}

    def create_user(self, data):
        fields = validate_new_user(data)
        if User.by_email(fields["email"]):
            raise ConflictError("Email já cadastrado")

        user = User()
        user.name, user.email, user.role = fields["name"], fields["email"], fields["role"]
        user.set_password(fields["password"])
        self._session.add(user)
        self._session.commit()
        logger.info("Usuário criado: %s", user.id)
        return user.to_dict()

    def update_user(self, user_id, data):
        user = self._get_or_404(user_id)
        fields = validate_user_update(data)

        if "email" in fields:
            existing = User.by_email(fields["email"])
            if existing and existing.id != user_id:
                raise ConflictError("Email já cadastrado")
        if "password" in fields:
            user.set_password(fields.pop("password"))
        for key, value in fields.items():
            setattr(user, key, value)

        self._session.commit()
        return user.to_dict()

    def delete_user(self, user_id):
        user = self._get_or_404(user_id)
        Task.delete_by_user(user_id)
        self._session.delete(user)
        self._session.commit()
        logger.info("Usuário deletado: %s", user_id)

    def user_tasks(self, user_id):
        self._get_or_404(user_id)
        return [task.to_user_task_dict() for task in Task.by_user(user_id)]

    def login(self, data):
        email, password = validate_login(data)
        user = User.by_email(email)
        if not user or not user.check_password(password):
            raise UnauthorizedError("Credenciais inválidas")
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        self._session.commit()  # persiste eventual migração do hash legado
        return {
            "message": "Login realizado com sucesso",
            "user": user.to_dict(),
            "token": self._tokens.issue(user),
        }
