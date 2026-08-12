"""Acesso a dados (persistência) do domínio de pedidos."""

from database import get_db


def criar_pedido(usuario_id, itens):
    """Cria um pedido com seus itens. `itens` já validados pelo service.

    Usa uma única transação e queries parametrizadas (sem N+1/concatenação).
    """
    db = get_db()
    cursor = db.cursor()
    total = sum(item["preco_unitario"] * item["quantidade"] for item in itens)

    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid

    for item in itens:
        cursor.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
            "VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )
        cursor.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def get_pedidos_por_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    rows = cursor.fetchall()
    return [_pedido_com_itens(r) for r in rows]


def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    rows = cursor.fetchall()
    return [_pedido_com_itens(r) for r in rows]


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = cursor.fetchone()[0]

    status_counts = {}
    for status in ("pendente", "aprovado", "cancelado"):
        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", (status,))
        status_counts[status] = cursor.fetchone()[0]

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "pedidos_pendentes": status_counts["pendente"],
        "pedidos_aprovados": status_counts["aprovado"],
        "pedidos_cancelados": status_counts["cancelado"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def _pedido_com_itens(pedido):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT ip.produto_id, ip.quantidade, ip.preco_unitario, p.nome AS produto_nome
           FROM itens_pedido ip
           LEFT JOIN produtos p ON p.id = ip.produto_id
           WHERE ip.pedido_id = ?""",
        (pedido["id"],),
    )
    itens = [
        {
            "produto_id": r["produto_id"],
            "produto_nome": r["produto_nome"] or "Desconhecido",
            "quantidade": r["quantidade"],
            "preco_unitario": r["preco_unitario"],
        }
        for r in cursor.fetchall()
    ]
    return {
        "id": pedido["id"],
        "usuario_id": pedido["usuario_id"],
        "status": pedido["status"],
        "total": pedido["total"],
        "criado_em": pedido["criado_em"],
        "itens": itens,
    }