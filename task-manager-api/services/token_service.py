"""Emissão/validação de tokens de autenticação assinados (itsdangerous já é dependência do Flask)."""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from utils.errors import UnauthorizedError


class TokenService:
    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age_seconds

    def issue(self, user):
        return self._serializer.dumps({"user_id": user.id, "role": user.role})

    def verify(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)
        except SignatureExpired:
            raise UnauthorizedError("Token expirado")
        except BadSignature:
            raise UnauthorizedError("Token inválido")
