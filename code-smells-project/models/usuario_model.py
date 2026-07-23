from core.db import get_db


def _row_to_public_dict(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def list_all():
    db = get_db()
    rows = db.execute("SELECT * FROM usuarios").fetchall()
    return [_row_to_public_dict(r) for r in rows]


def get_by_id(usuario_id):
    db = get_db()
    row = db.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _row_to_public_dict(row) if row else None


def get_with_password_by_email(email):
    db = get_db()
    return db.execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()


def create(nome, email, senha_hash, tipo="cliente"):
    db = get_db()
    cur = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cur.lastrowid
