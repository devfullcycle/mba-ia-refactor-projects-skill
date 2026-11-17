from config.constants import STATUS_PENDENTE
from database import get_db

_SELECT_PEDIDOS_COM_ITENS = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           i.produto_id, i.quantidade, i.preco_unitario, pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = i.produto_id
"""


def criar(usuario_id, total, itens):
    """Cria pedido + itens e baixa estoque numa única transação.

    `itens` é uma lista de tuplas (produto_id, quantidade, preco_unitario).
    """
    db = get_db()
    try:
        cur = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        )
        pedido_id = cur.lastrowid
        for produto_id, quantidade, preco_unitario in itens:
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, produto_id, quantidade, preco_unitario),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto_id),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise
    return pedido_id


def _agrupar(rows):
    pedidos = {}
    for row in rows:
        pedido = pedidos.get(row["pedido_id"])
        if pedido is None:
            pedido = {
                "id": row["pedido_id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            pedidos[row["pedido_id"]] = pedido
        if row["produto_id"] is not None:
            pedido["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"],
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return list(pedidos.values())


def listar_todos():
    rows = get_db().execute(_SELECT_PEDIDOS_COM_ITENS + " ORDER BY p.id, i.id").fetchall()
    return _agrupar(rows)


def listar_por_usuario(usuario_id):
    rows = get_db().execute(
        _SELECT_PEDIDOS_COM_ITENS + " WHERE p.usuario_id = ? ORDER BY p.id, i.id",
        (usuario_id,),
    ).fetchall()
    return _agrupar(rows)


def existe(pedido_id):
    row = get_db().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone()
    return row is not None


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
