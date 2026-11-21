"""Hash e verificação de senhas (werkzeug.security)."""
import hmac

from werkzeug.security import check_password_hash, generate_password_hash

PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def hash_senha(senha):
    return generate_password_hash(senha)


def _e_hash(armazenado):
    return armazenado.startswith(PREFIXOS_HASH)


def verificar_senha(senha, armazenado):
    """Retorna (valida, precisa_rehash). Senhas legadas em texto puro são aceitas uma vez e re-hasheadas."""
    armazenado = armazenado or ""
    if _e_hash(armazenado):
        return check_password_hash(armazenado, senha), False
    return hmac.compare_digest(senha.encode(), armazenado.encode()), True
