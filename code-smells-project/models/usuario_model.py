from config.constants import TIPO_USUARIO_PADRAO
from database import get_db

COLUNAS = "id, nome, email, senha, tipo, criado_em"


def listar_todos():
    rows = get_db().execute(f"SELECT {COLUNAS} FROM usuarios").fetchall()
    return [dict(r) for r in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute(
        f"SELECT {COLUNAS} FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    return dict(row) if row else None


def buscar_por_email(email):
    row = get_db().execute(
        f"SELECT {COLUNAS} FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    return dict(row) if row else None


def criar(nome, email, senha_hash, tipo=TIPO_USUARIO_PADRAO):
    db = get_db()
    cur = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cur.lastrowid


def atualizar_senha(usuario_id, senha_hash):
    db = get_db()
    db.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (senha_hash, usuario_id))
    db.commit()
