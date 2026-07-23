"""Password and signed-token adapters."""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

from store.domain.errors import AuthenticationError
from store.domain.models import Actor


class PasswordHasher:
    def hash(self, password: str) -> str:
        return generate_password_hash(password)

    def verify(self, stored_hash: str, password: str) -> bool:
        try:
            return check_password_hash(stored_hash, password)
        except (ValueError, TypeError):
            return False

    def is_hash(self, value: str) -> bool:
        return isinstance(value, str) and (value.startswith("scrypt:") or value.startswith("pbkdf2:"))


class TokenService:
    def __init__(self, secret_key: str, max_age: int):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="loja-api-auth")
        self._max_age = max_age

    def issue(self, user: dict) -> str:
        return self._serializer.dumps({"sub": int(user["id"]), "role": user["tipo"], "email": user["email"]})

    def verify(self, token: str) -> Actor:
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
            return Actor(int(payload["sub"]), str(payload["role"]), str(payload["email"]))
        except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError) as exc:
            raise AuthenticationError("Token inválido ou expirado") from exc
