from werkzeug.security import check_password_hash, generate_password_hash

from src.config.database import get_db

# A senha nunca faz parte da representação pública do usuário.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
PREFIXOS_HASH = ("scrypt:", "pbkdf2:")


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def autenticar(email, senha):
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    return {"id": row["id"], "nome": row["nome"], "email": row["email"], "tipo": row["tipo"]}


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    with db:
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
    return cursor.lastrowid


def migrar_senhas_legadas():
    """Converte senhas gravadas em texto plano pela versão anterior para hash."""
    db = get_db()
    rows = db.execute("SELECT id, senha FROM usuarios").fetchall()
    legadas = [row for row in rows if row["senha"] and not row["senha"].startswith(PREFIXOS_HASH)]
    with db:
        for row in legadas:
            db.execute(
                "UPDATE usuarios SET senha = ? WHERE id = ?",
                (generate_password_hash(row["senha"]), row["id"]),
            )
    return len(legadas)
