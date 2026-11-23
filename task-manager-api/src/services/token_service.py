from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class TokenService:
    """Signed, expiring auth tokens (itsdangerous ships with Flask — no new dependency)."""

    def __init__(self, secret_key, max_age):
        self._serializer = URLSafeTimedSerializer(secret_key, salt="auth-token")
        self._max_age = max_age

    def issue(self, user_id):
        return self._serializer.dumps({"uid": user_id})

    def verify(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)["uid"]
        except (BadSignature, SignatureExpired, KeyError, TypeError):
            return None
