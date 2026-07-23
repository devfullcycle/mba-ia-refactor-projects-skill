from core.db import get_db


def create(usuario_id, total):
    db = get_db()
    cur = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, "pendente", total),
    )
    db.commit()
    return cur.lastrowid


def update_status(pedido_id, novo_status):
    db = get_db()
    db.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
    )
    db.commit()


def _fetch_with_items(rows):
    db = get_db()
    result = []
    for row in rows:
        items = db.execute(
            """
            SELECT ip.produto_id, p.nome AS produto_nome,
                   ip.quantidade, ip.preco_unitario
              FROM itens_pedido ip
              JOIN produtos p ON p.id = ip.produto_id
             WHERE ip.pedido_id = ?
            """,
            (row["id"],),
        ).fetchall()
        result.append(
            {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [
                    {
                        "produto_id": it["produto_id"],
                        "produto_nome": it["produto_nome"],
                        "quantidade": it["quantidade"],
                        "preco_unitario": it["preco_unitario"],
                    }
                    for it in items
                ],
            }
        )
    return result


def list_by_user(usuario_id):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)
    ).fetchall()
    return _fetch_with_items(rows)


def list_all():
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos").fetchall()
    return _fetch_with_items(rows)
