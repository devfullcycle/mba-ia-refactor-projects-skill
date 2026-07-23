"""Emissão e validação de tokens assinados da aplicação."""

from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class InvalidAuthToken(ValueError):
    pass


class ExpiredAuthToken(InvalidAuthToken):
    pass


class AuthService:
    def __init__(self, secret_key: str, ttl_seconds: int = 3600):
        self._serializer = URLSafeTimedSerializer(
            secret_key=secret_key,
            salt="task-manager-auth-v1",
        )
        self._ttl_seconds = ttl_seconds

    def issue_token(self, user_id: int) -> str:
        return self._serializer.dumps({"sub": user_id})

    def verify_token(self, token: str) -> int:
        try:
            payload = self._serializer.loads(token, max_age=self._ttl_seconds)
        except SignatureExpired as exc:
            raise ExpiredAuthToken("Token expirado") from exc
        except BadSignature as exc:
            raise InvalidAuthToken("Token inválido") from exc

        user_id = payload.get("sub") if isinstance(payload, dict) else None
        if not isinstance(user_id, int):
            raise InvalidAuthToken("Token inválido")
        return user_id
