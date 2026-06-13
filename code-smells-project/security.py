import base64
import binascii
import hashlib
import hmac
import secrets


PBKDF2_ITERATIONS = 210000
PASSWORD_ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt_bytes = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, iterations)
    encoded_salt = base64.urlsafe_b64encode(salt_bytes).decode("ascii")
    encoded_digest = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{PASSWORD_ALGORITHM}${iterations}${encoded_salt}${encoded_digest}"


def verify_password(password: str, stored_value: str) -> bool:
    if not stored_value:
        return False

    if stored_value.startswith(f"{PASSWORD_ALGORITHM}$"):
        try:
            _, iterations, encoded_salt, encoded_digest = stored_value.split("$", 3)
            salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
            expected = base64.urlsafe_b64decode(encoded_digest.encode("ascii"))
            derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
            return hmac.compare_digest(derived, expected)
        except (ValueError, TypeError, binascii.Error):
            return False

    return hmac.compare_digest(password, stored_value)


def admin_token_is_valid(provided_token: str | None, expected_token: str | None) -> bool:
    if not expected_token:
        return False
    return hmac.compare_digest(provided_token or "", expected_token)
