class PedidoModel:
    """Acesso a dados de pedidos e itens. Listagens usam JOIN (sem N+1)."""

    def __init__(self, conn):
        self._conn = conn

    def criar(self, usuario_id, total, linhas):
        """Cria o pedido e seus itens em uma transação. `linhas` =
        lista de (produto_id, quantidade, preco_unitario)."""
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        pedido_id = cursor.lastrowid
        for produto_id, quantidade, preco in linhas:
            cursor.execute(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                (pedido_id, produto_id, quantidade, preco),
            )
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                (quantidade, produto_id),
            )
        self._conn.commit()
        return pedido_id

    def listar(self, usuario_id=None):
        cursor = self._conn.cursor()
        if usuario_id is not None:
            cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
        else:
            cursor.execute("SELECT * FROM pedidos")

        pedidos = {}
        for row in cursor.fetchall():
            pedidos[row["id"]] = {
                "id": row["id"],
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }

        if pedidos:
            ids = list(pedidos.keys())
            placeholders = ",".join("?" for _ in ids)
            cursor.execute(
                f"""
                SELECT ip.pedido_id, ip.produto_id, pr.nome AS produto_nome,
                       ip.quantidade, ip.preco_unitario
                FROM itens_pedido ip
                LEFT JOIN produtos pr ON pr.id = ip.produto_id
                WHERE ip.pedido_id IN ({placeholders})
                """,
                tuple(ids),
            )
            for item in cursor.fetchall():
                pedidos[item["pedido_id"]]["itens"].append({
                    "produto_id": item["produto_id"],
                    "produto_nome": item["produto_nome"] if item["produto_nome"] else "Desconhecido",
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                })

        return list(pedidos.values())

    def atualizar_status(self, pedido_id, novo_status):
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id),
        )
        self._conn.commit()
        return True

    def estatisticas(self):
        cursor = self._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(total) FROM pedidos")
        faturamento = cursor.fetchone()[0] or 0
        cursor.execute(
            "SELECT status, COUNT(*) FROM pedidos GROUP BY status"
        )
        por_status = {row[0]: row[1] for row in cursor.fetchall()}
        return total, faturamento, por_status

    def contagens(self):
        cursor = self._conn.cursor()
        counts = {}
        for tabela in ("produtos", "usuarios", "pedidos"):
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            counts[tabela] = cursor.fetchone()[0]
        return counts

    def reset(self):
        cursor = self._conn.cursor()
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            cursor.execute(f"DELETE FROM {tabela}")
        self._conn.commit()
