"""User use cases: CRUD, user tasks and login."""
import logging

from ..models.user_model import ROLE_ADMIN, ROLE_USER, User
from . import validators
from .errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError

logger = logging.getLogger(__name__)

MSG_CREDENTIALS_REQUIRED = "Email e senha são obrigatórios"
MSG_INVALID_CREDENTIALS = "Credenciais inválidas"
MSG_ADMIN_ONLY_ROLE = "Apenas administradores podem atribuir o papel admin"


class UserController:
    def __init__(self, users, tasks, token_service):
        self.users = users
        self.tasks = tasks
        self.token_service = token_service

    def list_users(self):
        return self.users.list_with_task_counts()

    def get_user(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user

    def get_user_with_tasks(self, user_id):
        user = self.get_user(user_id)
        return user, self.tasks.list_by_user(user_id)

    def list_user_tasks(self, user_id):
        self.get_user(user_id)
        return self.tasks.list_by_user(user_id)

    def create_user(self, data, actor_id=None):
        validators.require_payload(data)
        name = validators.require_text(data.get("name"), "Nome é obrigatório")
        email = validators.require_text(data.get("email"), "Email é obrigatório")
        password = validators.require_text(data.get("password"), "Senha é obrigatória")
        validators.validate_email(email)
        validators.validate_password(password)
        if self.users.get_by_email(email) is not None:
            raise ConflictError("Email já cadastrado")
        role = validators.validate_role(data.get("role", ROLE_USER))
        self._ensure_can_assign(role, actor_id)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        self.users.add(user)
        self.users.commit()
        logger.info("Usuário criado id=%s", user.id)
        return user

    def update_user(self, user_id, data, actor_id=None):
        user = self.get_user(user_id)
        validators.require_payload(data)
        if "name" in data:
            validators.require_text(data["name"], "Nome é obrigatório")
        if "email" in data:
            validators.validate_email(data["email"])
            existing = self.users.get_by_email(data["email"])
            if existing is not None and existing.id != user_id:
                raise ConflictError("Email já cadastrado")
        if "password" in data:
            validators.validate_password(data["password"])
        if "role" in data:
            self._ensure_can_assign(validators.validate_role(data["role"]), actor_id)
        if "active" in data:
            validators.validate_bool(data["active"], "Campo active deve ser booleano")

        for field in ("name", "email", "role", "active"):
            if field in data:
                setattr(user, field, data[field])
        if "password" in data:
            user.set_password(data["password"])
        self.users.commit()
        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        self.tasks.delete_by_user(user_id)  # same transaction as the user delete
        self.users.delete(user)
        self.users.commit()
        logger.info("Usuário deletado id=%s", user_id)

    def login(self, data):
        validators.require_payload(data)
        email, password = data.get("email"), data.get("password")
        if not email or not password:
            raise ValidationError(MSG_CREDENTIALS_REQUIRED)
        if not isinstance(email, str) or not isinstance(password, str):
            raise ValidationError(MSG_CREDENTIALS_REQUIRED)

        user = self.users.get_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError(MSG_INVALID_CREDENTIALS)
        self.users.commit()  # persists a transparent legacy-hash upgrade, if any
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        return user, self.token_service.issue(user.id)

    def _ensure_can_assign(self, role, actor_id):
        if role != ROLE_ADMIN:
            return
        actor = self.users.get(actor_id) if actor_id is not None else None
        if actor is None or not actor.active or not actor.is_admin():
            raise ForbiddenError(MSG_ADMIN_ONLY_ROLE)
