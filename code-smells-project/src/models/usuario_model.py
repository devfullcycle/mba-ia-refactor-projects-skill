import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from src.config.database import get_db
from src.models.base import row_to_dict

# A senha nunca faz parte da representação pública do usuário.
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")
PREFIXOS_HASH = ("scrypt:", "pbkdf2:")

TIPO_CLIENTE = "cliente"
TIPO_ADMIN = "admin"


class EmailDuplicadoError(Exception):
    pass


def _to_dict(row):
    return row_to_dict(row, CAMPOS_PUBLICOS)


def listar():
    rows = get_db().execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(row) for row in rows]


def buscar_por_id(usuario_id):
    row = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    return _to_dict(row) if row else None


def email_existe(email):
    row = get_db().execute("SELECT 1 FROM usuarios WHERE email = ? COLLATE NOCASE", (email,)).fetchone()
    return row is not None


def autenticar(email, senha):
    row = get_db().execute("SELECT * FROM usuarios WHERE email = ? COLLATE NOCASE", (email,)).fetchone()
    if row is None or not check_password_hash(row["senha"], senha):
        return None
    return _to_dict(row)


def criar(nome, email, senha, tipo=TIPO_CLIENTE):
    db = get_db()
    try:
        with db:
            cursor = db.execute(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                (nome, email, generate_password_hash(senha), tipo),
            )
    except sqlite3.IntegrityError as exc:
        # Garantido pelo índice único: cobre a corrida entre a checagem do controller e o INSERT.
        raise EmailDuplicadoError(email) from exc
    return cursor.lastrowid


def migrar_senhas_legadas():
    """Converte senhas gravadas em texto plano pela versão legada para hash."""
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
