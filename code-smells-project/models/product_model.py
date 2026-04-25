from database.connection import get_db


def serialize(row):
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


def get_all():
    db = get_db()
    rows = db.execute("SELECT * FROM produtos").fetchall()
    return [serialize(row) for row in rows]


def get_by_id(product_id):
    db = get_db()
    row = db.execute("SELECT * FROM produtos WHERE id = ?", [product_id]).fetchone()
    return serialize(row) if row else None


def create(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        [nome, descricao, preco, estoque, categoria],
    )
    db.commit()
    return cursor.lastrowid


def update(product_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    db.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        [nome, descricao, preco, estoque, categoria, product_id],
    )
    db.commit()


def delete(product_id):
    db = get_db()
    db.execute("DELETE FROM produtos WHERE id = ?", [product_id])
    db.commit()


def search(term, category=None, price_min=None, price_max=None):
    db = get_db()
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []

    if term:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([f"%{term}%", f"%{term}%"])
    if category:
        query += " AND categoria = ?"
        params.append(category)
    if price_min is not None:
        query += " AND preco >= ?"
        params.append(price_min)
    if price_max is not None:
        query += " AND preco <= ?"
        params.append(price_max)

    rows = db.execute(query, params).fetchall()
    return [serialize(row) for row in rows]


def get_by_ids(product_ids):
    if not product_ids:
        return {}
    db = get_db()
    placeholders = ",".join("?" * len(product_ids))
    rows = db.execute(
        f"SELECT * FROM produtos WHERE id IN ({placeholders})", product_ids
    ).fetchall()
    return {row["id"]: row for row in rows}


def update_stock(product_id, quantity):
    db = get_db()
    db.execute(
        "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
        [quantity, product_id],
    )
