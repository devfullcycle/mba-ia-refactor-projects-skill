from database import get_db

COLUNAS = "id, nome, descricao, preco, estoque, categoria, ativo, criado_em"


def listar_todos():
    rows = get_db().execute(f"SELECT {COLUNAS} FROM produtos").fetchall()
    return [dict(r) for r in rows]


def buscar_por_id(produto_id):
    row = get_db().execute(
        f"SELECT {COLUNAS} FROM produtos WHERE id = ?", (produto_id,)
    ).fetchone()
    return dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def buscar(termo, categoria=None, preco_min=None, preco_max=None):
    query = f"SELECT {COLUNAS} FROM produtos WHERE 1=1"
    params = []
    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        like = f"%{termo}%"
        params += [like, like]
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max:
        query += " AND preco <= ?"
        params.append(preco_max)
    rows = get_db().execute(query, params).fetchall()
    return [dict(r) for r in rows]
