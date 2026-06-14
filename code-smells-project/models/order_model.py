import sqlite3

VALID_STATUSES = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]


class OrderModel:
    def __init__(self, db):
        self.db = db

    def find_by_user(self, usuario_id):
        return self._fetch_orders("WHERE p.usuario_id = ?", (usuario_id,))

    def find_all(self):
        return self._fetch_orders("", ())

    def create(self, usuario_id, itens):
        cursor = self.db.cursor()
        try:
            cursor.execute("BEGIN")
            total = 0
            for item in itens:
                row = cursor.execute(
                    "SELECT * FROM produtos WHERE id = ?", (item["produto_id"],)
                ).fetchone()
                if row is None:
                    cursor.execute("ROLLBACK")
                    return {"erro": f"Produto {item['produto_id']} não encontrado"}
                if row["estoque"] < item["quantidade"]:
                    cursor.execute("ROLLBACK")
                    return {"erro": f"Estoque insuficiente para {row['nome']}"}
                total += row["preco"] * item["quantidade"]

            cursor.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
                (usuario_id, total),
            )
            pedido_id = cursor.lastrowid

            for item in itens:
                preco_row = cursor.execute(
                    "SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],)
                ).fetchone()
                cursor.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], preco_row["preco"]),
                )
                cursor.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )

            cursor.execute("COMMIT")
            return {"pedido_id": pedido_id, "total": total}
        except sqlite3.Error as e:
            cursor.execute("ROLLBACK")
            return {"erro": f"Erro ao criar pedido: {str(e)}"}

    def update_status(self, pedido_id, novo_status):
        self.db.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        self.db.commit()

    def sales_report(self):
        total_pedidos = self.db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        faturamento = self.db.execute(
            "SELECT COALESCE(SUM(total), 0) FROM pedidos"
        ).fetchone()[0]
        pendentes = self.db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'"
        ).fetchone()[0]
        aprovados = self.db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'"
        ).fetchone()[0]
        cancelados = self.db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'"
        ).fetchone()[0]
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }

    def _fetch_orders(self, where_clause, params):
        sql = f"""
            SELECT
                p.id, p.usuario_id, p.status, p.total, p.criado_em,
                ip.produto_id, ip.quantidade, ip.preco_unitario,
                prod.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
            LEFT JOIN produtos prod ON prod.id = ip.produto_id
            {where_clause}
            ORDER BY p.id
        """
        rows = self.db.execute(sql, params).fetchall()

        orders = {}
        for row in rows:
            oid = row["id"]
            if oid not in orders:
                orders[oid] = {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
            if row["produto_id"] is not None:
                orders[oid]["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or "Desconhecido",
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(orders.values())
