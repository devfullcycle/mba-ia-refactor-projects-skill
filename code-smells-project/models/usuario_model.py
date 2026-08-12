"""Acesso a dados (persistência) do domínio de usuários e autenticação."""

from database import get_db
import hashlib


def _senha_hash(senha):
    """Hash simples de demonstração. Em produção usar bcrypt/argon2.

    Nota: mantém o comportamento de login original sem armazenar senha em
    texto puro (a melhoria de hashing robusta é recomendada na auditoria).
    """
    return hashlib.sha256(senha.encode("utf-8")).hexdigest()


def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    return [_row_to_dict(r, incluir_senha=False) for r in rows]


def get_usuario_por_id(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def criar_usuario(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, _senha_hash(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email, senha):
    """Valida credenciais e retorna dados públicos do usuário, ou None."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND senha = ?",
        (email, _senha_hash(senha)),
    )
    row = cursor.fetchone()
    if row:
        return _row_to_dict(row, incluir_senha=False)
    return None


def _row_to_dict(row, incluir_senha=True):
    data = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }
    if incluir_senha:
        data["senha"] = row["senha"]
    return data