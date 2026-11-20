"""Hash de senhas com Werkzeug (scrypt), com suporte a upgrade de registros legados em texto puro."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

_PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


class PasswordHasher:
    def hash(self, senha: str) -> str:
        return generate_password_hash(senha)

    def is_hashed(self, armazenada: str) -> bool:
        return bool(armazenada) and armazenada.startswith(_PREFIXOS_HASH)

    def verify(self, armazenada: str, senha: str) -> bool:
        if not armazenada:
            return False
        if self.is_hashed(armazenada):
            return check_password_hash(armazenada, senha)
        # registro legado (texto puro): compara em tempo constante; o chamador faz o upgrade
        return hmac.compare_digest(armazenada.encode(), senha.encode())
