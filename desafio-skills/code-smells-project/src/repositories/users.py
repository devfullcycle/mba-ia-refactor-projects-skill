from src.database import get_db


def get_todos_usuarios():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    rows = cur.fetchall()
    return [
        {
            "id": r["id"],
            "nome": r["nome"],
            "email": r["email"],
            "tipo": r["tipo"],
            "criado_em": r["criado_em"],
        }
        for r in rows
    ]


def get_usuario_por_id(uid):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (uid,))
    row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def login_usuario(email, senha):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, nome, email, tipo FROM usuarios WHERE email = ? AND senha = ?", (email, senha))
    row = cur.fetchone()
    if row:
        return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}
    return None


def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha, tipo),
    )
    db.commit()
    return cur.lastrowid
