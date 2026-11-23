import logging

from src.controllers import validators
from src.controllers.errors import (
    ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError,
)
from src.models.user_model import PRIVILEGED_ROLES, ROLE_USER, User

logger = logging.getLogger(__name__)

USER_NOT_FOUND = "Usuário não encontrado"
EMAIL_TAKEN = "Email já cadastrado"
INVALID_CREDENTIALS = "Credenciais inválidas"
PRIVILEGED_FIELDS = ("role", "active")


def require_admin(caller, message):
    """AP-04 guard for conditional operations: 401 anonymous, 403 non-admin."""
    if caller is None:
        raise UnauthorizedError("Autenticação necessária")
    if not caller.is_admin():
        raise ForbiddenError(message)


class UserController:
    def __init__(self, users, tasks, tokens):
        self.users = users
        self.tasks = tasks
        self.tokens = tokens

    def list_users(self):
        counts = self.tasks.count_by_user()
        return [(user, counts.get(user.id, (0, 0))[0]) for user in self.users.list_all()]

    def get_user(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError(USER_NOT_FOUND)
        return user

    def get_user_with_tasks(self, user_id):
        user = self.get_user(user_id)
        return user, self.tasks.list_by_user(user_id)

    def list_user_tasks(self, user_id):
        self.get_user(user_id)
        return self.tasks.list_by_user(user_id)

    def create_user(self, data, caller):
        data = validators.require_body(data)
        role = data.get("role", ROLE_USER)
        if role in PRIVILEGED_ROLES:
            require_admin(caller, "Apenas administradores podem criar usuários com role privilegiado")

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        if not name:
            raise ValidationError("Nome é obrigatório")
        if not email:
            raise ValidationError("Email é obrigatório")
        if not password:
            raise ValidationError("Senha é obrigatória")
        validators.validate_name(name)
        validators.validate_email(email)
        validators.validate_password(password, "Senha deve ter no mínimo 4 caracteres")
        if self.users.get_by_email(email) is not None:
            raise ConflictError(EMAIL_TAKEN)
        validators.validate_role(role)

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        self.users.add(user)
        self.users.commit()
        logger.info("Usuário criado id=%s", user.id)
        return user

    def update_user(self, user_id, data, caller):
        if isinstance(data, dict) and any(field in data for field in PRIVILEGED_FIELDS):
            require_admin(caller, "Apenas administradores podem alterar role/active")
        user = self.get_user(user_id)
        data = validators.require_body(data)

        if "name" in data:
            user.name = validators.validate_name(data["name"])
        if "email" in data:
            email = validators.validate_email(data["email"])
            existing = self.users.get_by_email(email)
            if existing is not None and existing.id != user_id:
                raise ConflictError(EMAIL_TAKEN)
            user.email = email
        if "password" in data:
            user.set_password(validators.validate_password(data["password"], "Senha muito curta"))
        if "role" in data:
            user.role = validators.validate_role(data["role"])
        if "active" in data:
            user.active = validators.validate_active(data["active"])

        self.users.commit()
        logger.info("Usuário atualizado id=%s", user.id)
        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        self.tasks.delete_by_user(user_id)  # same transaction as the user removal
        self.users.delete(user)
        self.users.commit()
        logger.info("Usuário deletado id=%s", user_id)

    def login(self, data):
        data = validators.require_body(data)
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            raise ValidationError("Email e senha são obrigatórios")
        if not isinstance(email, str) or not isinstance(password, str):
            raise UnauthorizedError(INVALID_CREDENTIALS)

        user = self.users.get_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError(INVALID_CREDENTIALS)
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        self.users.commit()  # persists a transparent legacy-hash upgrade, if any
        return user, self.tokens.issue(user.id)
