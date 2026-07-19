"""Model de Usuário — hashing de senha e SQL parametrizado. Nunca expõe a senha."""
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db


def _serializar_publico(row):
    # A senha (hash) jamais é serializada na resposta.
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def listar_todos():
    db = get_db()
    rows = db.execute("SELECT * FROM usuarios").fetchall()
    return [_serializar_publico(r) for r in rows]


def buscar_por_id(id):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (id,)).fetchone()
    return _serializar_publico(row) if row else None


def autenticar(email, senha):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row and check_password_hash(row["senha"], senha):
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }
    return None


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid
