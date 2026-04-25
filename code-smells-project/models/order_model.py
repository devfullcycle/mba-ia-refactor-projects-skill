from database.connection import get_db


def _build_orders_with_items(rows):
    orders = {}
    for row in rows:
        order_id = row["id"]
        if order_id not in orders:
            orders[order_id] = {
                "id": order_id,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
        if row["produto_id"] is not None:
            orders[order_id]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(orders.values())


ORDERS_JOIN_QUERY = """
    SELECT o.id, o.usuario_id, o.status, o.total, o.criado_em,
           oi.produto_id, oi.quantidade, oi.preco_unitario,
           p.nome as produto_nome
    FROM pedidos o
    LEFT JOIN itens_pedido oi ON oi.pedido_id = o.id
    LEFT JOIN produtos p ON p.id = oi.produto_id
"""


def get_all():
    db = get_db()
    rows = db.execute(ORDERS_JOIN_QUERY + " ORDER BY o.id").fetchall()
    return _build_orders_with_items(rows)


def get_by_user(usuario_id):
    db = get_db()
    rows = db.execute(
        ORDERS_JOIN_QUERY + " WHERE o.usuario_id = ? ORDER BY o.id",
        [usuario_id],
    ).fetchall()
    return _build_orders_with_items(rows)


def create(usuario_id, items, product_lookup):
    db = get_db()
    total = sum(
        product_lookup[item["produto_id"]]["preco"] * item["quantidade"]
        for item in items
    )

    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        [usuario_id, total],
    )
    pedido_id = cursor.lastrowid

    for item in items:
        product = product_lookup[item["produto_id"]]
        db.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            [pedido_id, item["produto_id"], item["quantidade"], product["preco"]],
        )

    for item in items:
        db.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            [item["quantidade"], item["produto_id"]],
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def update_status(pedido_id, novo_status):
    db = get_db()
    db.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        [novo_status, pedido_id],
    )
    db.commit()
