from werkzeug.security import generate_password_hash, check_password_hash
from database.connection import get_db


def serialize_public(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_all():
    db = get_db()
    rows = db.execute("SELECT * FROM usuarios").fetchall()
    return [serialize_public(row) for row in rows]


def get_by_id(user_id):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", [user_id]).fetchone()
    return serialize_public(row) if row else None


def create(nome, email, senha, tipo="cliente"):
    db = get_db()
    hashed = generate_password_hash(senha)
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [nome, email, hashed, tipo],
    )
    db.commit()
    return cursor.lastrowid


def authenticate(email, senha):
    db = get_db()
    row = db.execute(
        "SELECT * FROM usuarios WHERE email = ?", [email]
    ).fetchone()
    if row and check_password_hash(row["senha"], senha):
        return serialize_public(row)
    return None
