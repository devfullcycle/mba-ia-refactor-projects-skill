"""Repository de usuários — único ponto de acesso à tabela `usuarios`.

Queries parametrizadas (SEC-01). O campo `senha` nunca sai em `listar`/
`buscar_por_id`; a verificação de credencial usa `buscar_por_email`, que
devolve o hash apenas para o service de autenticação.
"""

from database import get_db

_COLUNAS_PUBLICAS = "id, nome, email, tipo, criado_em"


def _to_public_dict(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar():
    cursor = get_db().cursor()
    cursor.execute(f"SELECT {_COLUNAS_PUBLICAS} FROM usuarios")
    return [_to_public_dict(row) for row in cursor.fetchall()]


def buscar_por_id(usuario_id):
    cursor = get_db().cursor()
    cursor.execute(f"SELECT {_COLUNAS_PUBLICAS} FROM usuarios WHERE id = ?", (usuario_id,))
    return _to_public_dict(cursor.fetchone())


def buscar_por_email(email):
    """Uso interno da autenticação: inclui o hash da senha."""
    cursor = get_db().cursor()
    cursor.execute("SELECT id, nome, email, senha, tipo FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": row["senha"],
        "tipo": row["tipo"],
    }


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha, tipo),
    )
    db.commit()
    return cursor.lastrowid


def contar():
    cursor = get_db().cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    return cursor.fetchone()[0]
