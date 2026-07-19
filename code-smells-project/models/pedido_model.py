"""Model de Pedido — regra de negócio (estoque/total), transação atômica e leitura sem N+1."""
from database import get_db


def _validar_e_calcular_total(db, itens):
    """Valida existência/estoque e calcula o total. Retorna (total, erro)."""
    total = 0
    for item in itens:
        produto = db.execute(
            "SELECT * FROM produtos WHERE id = ?", (item["produto_id"],)
        ).fetchone()
        if produto is None:
            return None, {"erro": "Produto " + str(item["produto_id"]) + " não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return None, {"erro": "Estoque insuficiente para " + produto["nome"]}
        total += produto["preco"] * item["quantidade"]
    return total, None


def criar(usuario_id, itens):
    db = get_db()
    total, erro = _validar_e_calcular_total(db, itens)
    if erro:
        return erro

    try:
        cursor = db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for item in itens:
            produto = db.execute(
                "SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],)
            ).fetchone()
            db.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                "VALUES (?, ?, ?, ?)",
                (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
            )
            db.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (item["quantidade"], item["produto_id"]),
            )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"pedido_id": pedido_id, "total": total}


def _carregar_itens(db, pedido_ids):
    """Carrega todos os itens de vários pedidos numa única query (evita N+1)."""
    if not pedido_ids:
        return {}
    placeholders = ",".join("?" for _ in pedido_ids)
    rows = db.execute(
        "SELECT ip.pedido_id, ip.produto_id, ip.quantidade, ip.preco_unitario, "
        "p.nome AS produto_nome "
        "FROM itens_pedido ip LEFT JOIN produtos p ON p.id = ip.produto_id "
        "WHERE ip.pedido_id IN (" + placeholders + ")",
        pedido_ids,
    ).fetchall()

    itens_por_pedido = {}
    for r in rows:
        itens_por_pedido.setdefault(r["pedido_id"], []).append(
            {
                "produto_id": r["produto_id"],
                "produto_nome": r["produto_nome"] if r["produto_nome"] else "Desconhecido",
                "quantidade": r["quantidade"],
                "preco_unitario": r["preco_unitario"],
            }
        )
    return itens_por_pedido


def _montar_pedidos(rows, itens_por_pedido):
    return [
        {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": itens_por_pedido.get(row["id"], []),
        }
        for row in rows
    ]


def listar_por_usuario(usuario_id):
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,)).fetchall()
    itens = _carregar_itens(db, [r["id"] for r in rows])
    return _montar_pedidos(rows, itens)


def listar_todos():
    db = get_db()
    rows = db.execute("SELECT * FROM pedidos").fetchall()
    itens = _carregar_itens(db, [r["id"] for r in rows])
    return _montar_pedidos(rows, itens)


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()
    return True
