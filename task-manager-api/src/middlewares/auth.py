"""Authentication helpers: resolve the caller from an `Authorization: Bearer <token>` header."""
from flask import request

BEARER_SCHEME = "bearer"


def authenticated_user_id(token_service):
    """User id of the caller when a valid signed token is sent; None for anonymous calls."""
    scheme, _, token = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() != BEARER_SCHEME or not token.strip():
        return None
    return token_service.verify(token.strip())
