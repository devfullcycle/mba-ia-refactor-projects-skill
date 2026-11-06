"""Service de usuários e autenticação.

SEC-03: senhas são armazenadas e verificadas exclusivamente via hash com salt
(`werkzeug.security`). O seed já é gravado com hash e registros legados em
texto puro são re-hasheados no boot por
`database.schema.migrate_legacy_passwords`. O login nunca compara texto puro e
o campo `senha` nunca é devolvido nas respostas.
"""

from werkzeug.security import check_password_hash, generate_password_hash

from errors import NaoAutorizadoError, NaoEncontradoError
from repositories import usuario_repository

_PREFIXOS_HASH = ("pbkdf2:", "scrypt:", "argon2")


def listar():
    return usuario_repository.listar()


def buscar_por_id(usuario_id):
    usuario = usuario_repository.buscar_por_id(usuario_id)
    if usuario is None:
        raise NaoEncontradoError("Usuário não encontrado")
    return usuario


def criar(dados):
    senha_hash = generate_password_hash(dados["senha"])
    usuario_id = usuario_repository.criar(dados["nome"], dados["email"], senha_hash)
    return {"id": usuario_id}


def autenticar(email, senha):
    usuario = usuario_repository.buscar_por_email(email)
    if usuario is None:
        raise NaoAutorizadoError("Email ou senha inválidos")

    stored = usuario["senha"] or ""
    if not _hash_valido(stored) or not check_password_hash(stored, senha):
        raise NaoAutorizadoError("Email ou senha inválidos")

    return {
        "id": usuario["id"],
        "nome": usuario["nome"],
        "email": usuario["email"],
        "tipo": usuario["tipo"],
    }


def _hash_valido(stored):
    """Só aceita armazenamento com prefixo de hash; texto puro falha fechado."""
    return isinstance(stored, str) and stored.startswith(_PREFIXOS_HASH)
