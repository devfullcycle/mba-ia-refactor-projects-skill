from .database import get_db

class PedidoModel:
    @classmethod
    def _agrupar_pedidos_com_itens(cls, rows):
        """Agrupa os resultados planos do JOIN em objetos de pedidos com seus itens."""
        pedidos_map = {}
        pedidos_ordem = []

        for row in rows:
            pedido_id = row["pedido_id"]
            if pedido_id not in pedidos_map:
                pedido = {
                    "id": pedido_id,
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": []
                }
                pedidos_map[pedido_id] = pedido
                pedidos_ordem.append(pedido)

            if row["item_id"] is not None:
                pedidos_map[pedido_id]["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] if row["produto_nome"] else "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"]
                })

        return pedidos_ordem

    @classmethod
    def listar_todos(cls):
        """Elimina o anti-pattern N+1 executando um único JOIN consolidado."""
        db = get_db()
        cursor = db.cursor()
        query = """
            SELECT 
                p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
                ip.id AS item_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                prod.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN produtos prod ON ip.produto_id = prod.id
            ORDER BY p.id DESC
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        return cls._agrupar_pedidos_com_itens(rows)

    @classmethod
    def listar_por_usuario(cls, usuario_id):
        """Elimina N+1 para pedidos de um usuário com query parametrizada e JOIN."""
        db = get_db()
        cursor = db.cursor()
        query = """
            SELECT 
                p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
                ip.id AS item_id, ip.produto_id, ip.quantidade, ip.preco_unitario,
                prod.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido ip ON p.id = ip.pedido_id
            LEFT JOIN produtos prod ON ip.produto_id = prod.id
            WHERE p.usuario_id = ?
            ORDER BY p.id DESC
        """
        cursor.execute(query, (usuario_id,))
        rows = cursor.fetchall()
        return cls._agrupar_pedidos_com_itens(rows)

    @classmethod
    def criar(cls, usuario_id, itens):
        """Criação atômica de pedido com validação transacional de estoque."""
        db = get_db()
        cursor = db.cursor()

        # Verificar se usuário existe
        cursor.execute("SELECT id FROM usuarios WHERE id = ?", (usuario_id,))
        if not cursor.fetchone():
            return {"erro": f"Usuário {usuario_id} não encontrado"}

        total = 0.0
        produtos_validados = []

        # Validação prévia de existência e estoque de todos os itens
        for item in itens:
            produto_id = item.get("produto_id")
            quantidade = item.get("quantidade", 0)

            if not produto_id or quantidade <= 0:
                return {"erro": "Dados inválidos nos itens do pedido"}

            cursor.execute("SELECT id, nome, preco, estoque FROM produtos WHERE id = ? AND ativo = 1", (produto_id,))
            produto = cursor.fetchone()

            if produto is None:
                return {"erro": f"Produto {produto_id} não encontrado"}
            if produto["estoque"] < quantidade:
                return {"erro": f"Estoque insuficiente para {produto['nome']}"}

            subtotal = produto["preco"] * quantidade
            total += subtotal
            produtos_validados.append({
                "produto_id": produto_id,
                "quantidade": quantidade,
                "preco_unitario": produto["preco"]
            })

        try:
            # Iniciar gravação atômica
            cursor.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, round(total, 2))
            )
            pedido_id = cursor.lastrowid

            for item in produtos_validados:
                cursor.execute(
                    """
                    INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                    VALUES (?, ?, ?, ?)
                    """,
                    (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"])
                )
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"])
                )

            db.commit()
            return {"pedido_id": pedido_id, "total": round(total, 2)}
        except Exception as e:
            db.rollback()
            raise e

    @classmethod
    def atualizar_status(cls, pedido_id, novo_status):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @classmethod
    def contar(cls):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        return cursor.fetchone()[0]
