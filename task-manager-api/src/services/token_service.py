"""Emissão e verificação de tokens de sessão.

O legado devolvia `'fake-jwt-token-' + str(user.id)`: previsível, forjável e nunca
verificado. Aqui o token é assinado com a `SECRET_KEY` e tem prazo de validade — usando
`itsdangerous`, que já vem com o Flask (nenhuma dependência nova).
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.middlewares.error_handler import UnauthorizedError

TOKEN_SALT = "task-manager-auth"


class TokenService:
    def __init__(self, secret_key, ttl_seconds=3600):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)
        self._ttl_seconds = ttl_seconds

    def issue(self, user):
        return self._serializer.dumps({"sub": user.id, "role": user.role})

    def verify(self, token):
        try:
            return self._serializer.loads(token, max_age=self._ttl_seconds)
        except SignatureExpired:
            raise UnauthorizedError("Token expirado")
        except BadSignature:
            raise UnauthorizedError("Token inválido")
