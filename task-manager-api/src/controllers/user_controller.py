"""User use cases, login and the authorization rules for account changes (AP-04)."""
import logging

from src.controllers import validators
from src.controllers.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from src.models.constants import ROLE_USER

logger = logging.getLogger(__name__)

PRIVILEGED_FIELDS = ("role", "active")      # admin only
CREDENTIAL_FIELDS = ("password", "email")   # the account owner or an admin


def _require_admin(caller, message):
    if caller is None:
        raise UnauthorizedError("Autenticação necessária")
    if not caller.is_admin():
        raise ForbiddenError(message)


def _require_owner_or_admin(caller, user_id, message):
    if caller is None:
        raise UnauthorizedError("Autenticação necessária")
    if caller.id != user_id and not caller.is_admin():
        raise ForbiddenError(message)


class UserController:
    def __init__(self, users, tasks, tokens):
        self.users = users
        self.tasks = tasks
        self.tokens = tokens

    def list_users(self):
        counts = self.tasks.count_by_user()
        return [(user, counts.get(user.id, 0)) for user in self.users.list_all()]

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

    def create_user(self, data, caller=None):
        validators.require_object(data)
        if "role" in data and data["role"] != ROLE_USER:
            _require_admin(caller, "Apenas administradores podem criar contas com role privilegiado")
        fields = validators.parse_user_create(data)
        if self.users.get_by_email(fields["email"]) is not None:
            raise ConflictError("Email já cadastrado")
        validators.validate_role(fields["role"])
        user = self.users.new(name=fields["name"], email=fields["email"], role=fields["role"])
        user.set_password(fields["password"])
        self.users.commit()
        logger.info("Usuário criado id=%s", user.id)
        return user

    def update_user(self, user_id, data, caller=None):
        user = self.get_user(user_id)
        validators.require_object(data)
        if any(field in data for field in PRIVILEGED_FIELDS):
            _require_admin(caller, "Apenas administradores podem alterar role/active")
        if any(field in data for field in CREDENTIAL_FIELDS):
            _require_owner_or_admin(
                caller, user_id, "Apenas o próprio usuário ou um administrador pode alterar senha/email"
            )
        fields = validators.parse_user_update(data)
        if "email" in fields:
            existing = self.users.get_by_email(fields["email"])
            if existing is not None and existing.id != user_id:
                raise ConflictError("Email já cadastrado")
        password = fields.pop("password", None)
        for name, value in fields.items():
            setattr(user, name, value)
        if password is not None:
            user.set_password(password)
        self.users.commit()
        logger.info("Usuário atualizado id=%s campos=%s", user_id, sorted(data.keys()))
        return user

    def delete_user(self, user_id):
        user = self.get_user(user_id)
        self.tasks.delete_by_user(user_id)   # same unit of work as the user delete
        self.users.delete(user)
        self.users.commit()
        logger.info("Usuário deletado id=%s", user_id)

    def login(self, data):
        email, password = validators.parse_login(data)
        user = self.users.get_by_email(email)
        if user is None:
            raise UnauthorizedError("Credenciais inválidas")
        valid, upgraded = user.verify_password(password)
        if not valid:
            raise UnauthorizedError("Credenciais inválidas")
        if upgraded:
            self.users.commit()
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        return user, self.tokens.issue(user.id)
