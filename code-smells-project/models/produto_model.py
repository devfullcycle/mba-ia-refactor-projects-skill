"""Model de Produto — acesso a dados com SQL parametrizado."""
from database import get_db

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _serializar(row):
    return {campo: row[campo] for campo in _CAMPOS}


def listar_todos():
    db = get_db()
    rows = db.execute("SELECT * FROM produtos").fetchall()
    return [_serializar(r) for r in rows]


def buscar_por_id(id):
    db = get_db()
    row = db.execute("SELECT * FROM produtos WHERE id = ?", (id,)).fetchone()
    return _serializar(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar(id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, id),
    )
    db.commit()
    return True


def deletar(id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (id,))
    db.commit()
    return True


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        like = "%" + termo + "%"
        params.extend([like, like])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)

    rows = db.execute(query, params).fetchall()
    return [_serializar(r) for r in rows]
