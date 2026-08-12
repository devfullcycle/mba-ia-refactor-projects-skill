"""Acesso a dados (persistência) do domínio de produtos."""

from database import get_db


def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos")
    rows = cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


def get_produto_por_id(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    return _row_to_dict(row) if row else None


def criar_produto(dados):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
        ),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(produto_id, dados):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
        "categoria = ? WHERE id = ?",
        (
            dados["nome"],
            dados.get("descricao", ""),
            dados["preco"],
            dados["estoque"],
            dados.get("categoria", "geral"),
            produto_id,
        ),
    )
    db.commit()
    return True


def deletar_produto(produto_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def buscar_produtos_por_filtro(termo=None, categoria=None, preco_min=None, preco_max=None):
    """Busca filtrada com queries parametrizadas (sem concatenação de strings)."""
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if termo:
        sql += " AND (nome LIKE ? OR descricao LIKE ?)"
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        sql += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        sql += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        sql += " AND preco <= ?"
        params.append(preco_max)

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    return [_row_to_dict(r) for r in rows]


def _row_to_dict(row):
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