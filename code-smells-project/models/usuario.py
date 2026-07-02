from utils.database import get_db
from werkzeug.security import generate_password_hash, check_password_hash

def listar_todos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios")
    rows = cursor.fetchall()
    return [_row_to_dict(row) for row in rows]

def buscar_por_id(id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None

def autenticar(email, senha):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()

    if row and check_password_hash(row["senha"], senha):
        return _row_to_dict(row, incluir_senha=False)
    return None

def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    senha_hash = generate_password_hash(senha)
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha_hash, tipo)
    )
    db.commit()
    return cursor.lastrowid

def _row_to_dict(row, incluir_senha=False):
    if row is None:
        return None
    dados = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"]
    }
    if incluir_senha:
        dados["senha"] = row["senha"]
    return dados
