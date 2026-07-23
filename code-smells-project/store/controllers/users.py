"""User registration and authentication use cases."""

from __future__ import annotations

from store.domain.errors import AuthenticationError
from store.domain.ports import PasswordHasherPort, UserRepositoryPort
from store.domain.policies import validate_login, validate_user_registration


class UserController:
    def __init__(
        self,
        repository: UserRepositoryPort,
        password_hasher: PasswordHasherPort,
    ):
        self.repository = repository
        self.password_hasher = password_hasher

    def list(self) -> list[dict]:
        return self.repository.list_all()

    def get(self, user_id: int) -> dict | None:
        return self.repository.get(user_id)

    def register(self, data: object) -> int:
        name, email, password = validate_user_registration(data)
        return self.repository.create(name, email, self.password_hasher.hash(password))

    def authenticate(self, data: object) -> dict:
        email, password = validate_login(data)
        user = self.repository.get_by_email(email)
        if user is None or not self.password_hasher.verify(user["senha"], password):
            raise AuthenticationError("Email ou senha inválidos")
        return user

    def get_for_token(self, user_id: int) -> dict | None:
        return self.repository.get(user_id)
