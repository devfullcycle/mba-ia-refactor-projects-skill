"""Signed, expiring authentication tokens (itsdangerous ships with Flask)."""
from itsdangerous import BadSignature, URLSafeTimedSerializer

TOKEN_SALT = "auth-token"


class TokenService:
    def __init__(self, secret_key, max_age_seconds):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)
        self._max_age = max_age_seconds

    def issue(self, user_id):
        return self._serializer.dumps({"uid": user_id})

    def verify(self, token):
        """Return the user id carried by a valid token, or None."""
        try:
            payload = self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:  # also covers SignatureExpired
            return None
        return payload.get("uid") if isinstance(payload, dict) else None
