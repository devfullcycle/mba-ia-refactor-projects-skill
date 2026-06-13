from database import get_db


def _produto_from_row(row):
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


def _usuario_public_from_row(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def _usuario_login_from_row(row):
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "senha": row["senha"],
        "tipo": row["tipo"],
    }


def _pedido_base_from_row(row):
    return {
        "id": row["pedido_id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }


def get_todos_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos ORDER BY id")
    return [_produto_from_row(row) for row in cursor.fetchall()]


def get_produto_por_id(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    return _produto_from_row(row) if row else None


def criar_produto(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO produtos (nome, descricao, preco, estoque, categoria)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(product_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE produtos
        SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
        WHERE id = ?
        """,
        (nome, descricao, preco, estoque, categoria, product_id),
    )
    db.commit()
    return cursor.rowcount


def deletar_produto(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
    db.commit()
    return cursor.rowcount


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    db = get_db()
    cursor = db.cursor()

    query = "SELECT * FROM produtos WHERE 1=1"
    params = []

    if termo:
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        like_term = f"%{termo}%"
        params.extend([like_term, like_term])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    query += " ORDER BY id"
    cursor.execute(query, params)
    return [_produto_from_row(row) for row in cursor.fetchall()]


def get_todos_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios ORDER BY id")
    return [_usuario_public_from_row(row) for row in cursor.fetchall()]


def get_usuario_por_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    return _usuario_public_from_row(row) if row else None


def get_usuario_com_senha_por_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    return _usuario_login_from_row(row) if row else None


def get_usuario_por_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
    row = cursor.fetchone()
    return _usuario_public_from_row(row) if row else None


def criar_usuario(nome, email, senha_hash, tipo="cliente"):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO usuarios (nome, email, senha, tipo)
        VALUES (?, ?, ?, ?)
        """,
        (nome, email, senha_hash, tipo),
    )
    db.commit()
    return cursor.lastrowid


def criar_pedido(usuario_id, itens):
    db = get_db()
    with db:
        cursor = db.cursor()
        total = 0.0
        prepared_items = []

        for item in itens:
            cursor.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
            produto = cursor.fetchone()
            if produto is None:
                raise LookupError(f"Produto {item['produto_id']} nao encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise ValueError(f"Estoque insuficiente para {produto['nome']}")
            prepared_items.append((produto, item["quantidade"]))
            total += float(produto["preco"]) * int(item["quantidade"])

        cursor.execute(
            """
            INSERT INTO pedidos (usuario_id, status, total)
            VALUES (?, 'pendente', ?)
            """,
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid

        for produto, quantidade in prepared_items:
            cursor.execute(
                """
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, produto["id"], quantidade, produto["preco"]),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto["id"]),
            )

    return {"pedido_id": pedido_id, "total": round(total, 2)}


def _group_pedidos(rows):
    pedidos = {}
    for row in rows:
        pedido_id = row["pedido_id"]
        pedido = pedidos.setdefault(pedido_id, _pedido_base_from_row(row))
        if row["item_id"] is not None:
            pedido["itens"].append(
                {
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                }
            )
    return list(pedidos.values())


def get_pedidos_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT
            p.id AS pedido_id,
            p.usuario_id,
            p.status,
            p.total,
            p.criado_em,
            i.id AS item_id,
            i.produto_id,
            i.quantidade,
            i.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
        WHERE p.usuario_id = ?
        ORDER BY p.id, i.id
        """,
        (usuario_id,),
    )
    return _group_pedidos(cursor.fetchall())


def get_todos_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT
            p.id AS pedido_id,
            p.usuario_id,
            p.status,
            p.total,
            p.criado_em,
            i.id AS item_id,
            i.produto_id,
            i.quantidade,
            i.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido i ON i.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = i.produto_id
        ORDER BY p.id, i.id
        """
    )
    return _group_pedidos(cursor.fetchall())


def relatorio_vendas():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM pedidos")
    total_pedidos = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total), 0) FROM pedidos")
    faturamento = float(cursor.fetchone()[0])

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("pendente",))
    pendentes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("aprovado",))
    aprovados = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", ("cancelado",))
    cancelados = cursor.fetchone()[0]

    desconto = 0.0
    if faturamento > 10000:
        desconto = faturamento * 0.1
    elif faturamento > 5000:
        desconto = faturamento * 0.05
    elif faturamento > 1000:
        desconto = faturamento * 0.02

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def atualizar_status_pedido(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()
    return cursor.rowcount


def count_produtos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM produtos")
    return cursor.fetchone()[0]


def count_usuarios():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    return cursor.fetchone()[0]


def count_pedidos():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    return cursor.fetchone()[0]


def reset_database():
    db = get_db()
    with db:
        cursor = db.cursor()
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")


def executar_query_leitura(query):
    sql = query.strip()
    if not sql.lower().startswith("select"):
        raise ValueError("Apenas consultas SELECT sao permitidas")

    db = get_db()
    cursor = db.cursor()
    cursor.execute(sql)
    return [dict(row) for row in cursor.fetchall()]
