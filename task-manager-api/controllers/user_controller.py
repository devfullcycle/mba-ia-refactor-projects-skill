from __future__ import annotations

from errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from models.user import User
from schemas.validators import validate_login, validate_user_create, validate_user_update
from services.auth_service import ExpiredAuthToken, InvalidAuthToken

from controllers.base import validate


class UserController:
    def __init__(self, users, tasks, session, auth_service):
        self.users = users
        self.tasks = tasks
        self.session = session
        self.auth_service = auth_service

    def list(self):
        return self.users.list_with_task_counts()

    def get(self, user_id):
        user = self.users.get_with_tasks(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user

    def create(self, payload):
        data = validate(validate_user_create, payload)
        if self.users.email_exists(data["email"]):
            raise ConflictError("Email já cadastrado")
        user = User(
            name=data["name"],
            email=data["email"],
            role=data["role"],
        )
        user.set_password(data["password"])
        self.users.add(user)
        self.session.commit()
        return user

    def update(self, user_id, payload):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        data = validate(validate_user_update, payload)
        email = data.get("email")
        if email and self.users.email_exists(email, excluding_user_id=user_id):
            raise ConflictError("Email já cadastrado")
        password = data.pop("password", None)
        for field, value in data.items():
            setattr(user, field, value)
        if password is not None:
            user.set_password(password)
        self.session.commit()
        return user

    def delete(self, user_id):
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        self.users.delete_with_tasks(user)
        self.session.commit()

    def list_tasks(self, user_id):
        if self.users.get(user_id) is None:
            raise NotFoundError("Usuário não encontrado")
        return self.tasks.list_by_user(user_id)

    def login(self, payload):
        credentials = validate(validate_login, payload)
        user = self.users.get_by_email(credentials["email"])
        if user is None:
            raise UnauthorizedError("Credenciais inválidas")
        legacy_hash = user._has_legacy_md5_password()
        if not user.check_password(credentials["password"]):
            raise UnauthorizedError("Credenciais inválidas")
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        if legacy_hash:
            self.session.commit()
        return user, self.auth_service.issue_token(user.id)

    def authenticate_token(self, token):
        try:
            user_id = self.auth_service.verify_token(token)
        except ExpiredAuthToken as error:
            raise UnauthorizedError("Token expirado") from error
        except InvalidAuthToken as error:
            raise UnauthorizedError("Token inválido") from error
        user = self.users.get(user_id)
        if user is None:
            raise UnauthorizedError("Token inválido")
        if not user.active:
            raise ForbiddenError("Usuário inativo")
        return user
