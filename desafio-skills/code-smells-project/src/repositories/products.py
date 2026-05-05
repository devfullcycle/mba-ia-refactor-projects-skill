from src.database import get_db


def _row_to_produto(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_todos_produtos():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM produtos")
    return [_row_to_produto(r) for r in cur.fetchall()]


def get_produto_por_id(pid):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM produtos WHERE id = ?", (pid,))
    return _row_to_produto(cur.fetchone())


def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO produtos (nome, descricao, preco, estoque, categoria)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def atualizar_produto(pid, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        """
        UPDATE produtos
        SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
        WHERE id = ?
        """,
        (nome, descricao, preco, estoque, categoria, pid),
    )
    db.commit()
    return True


def deletar_produto(pid):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM produtos WHERE id = ?", (pid,))
    db.commit()
    return True


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cur = db.cursor()
    parts = ["SELECT * FROM produtos WHERE 1=1"]
    params = []
    if termo:
        parts.append("AND (nome LIKE ? OR descricao LIKE ?)")
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        parts.append("AND categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        parts.append("AND preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        parts.append("AND preco <= ?")
        params.append(preco_max)
    sql = " ".join(parts)
    cur.execute(sql, params)
    return [_row_to_produto(r) for r in cur.fetchall()]
