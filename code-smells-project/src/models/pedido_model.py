"""Model de Pedido: persistência transacional, consultas agregadas e regras de venda."""

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (STATUS_PENDENTE, STATUS_APROVADO, "enviado", "entregue", STATUS_CANCELADO)

# (faturamento mínimo — exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = ((10000, 0.10), (5000, 0.05), (1000, 0.02))

PRODUTO_DESCONHECIDO = "Desconhecido"


def calcular_desconto(faturamento):
    for minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > minimo:
            return faturamento * taxa
    return 0


class PedidoModel:
    def __init__(self, get_connection):
        self._conn = get_connection

    def inserir(self, conn, usuario_id, total, itens_com_preco):
        """Insere pedido + itens usando a conexão/transação do chamador."""
        cursor = conn.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, STATUS_PENDENTE, total),
        )
        pedido_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            [(pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]) for item in itens_com_preco],
        )
        return pedido_id

    def listar(self, usuario_id=None):
        """Lista pedidos com itens em uma única query (sem N+1)."""
        rows = self._conn().execute(
            """
            SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,
                   i.id AS item_id, i.produto_id, i.quantidade, i.preco_unitario,
                   pr.nome AS produto_nome
            FROM pedidos p
            LEFT JOIN itens_pedido i ON i.pedido_id = p.id
            LEFT JOIN produtos pr ON pr.id = i.produto_id
            WHERE (? IS NULL OR p.usuario_id = ?)
            ORDER BY p.id, i.id
            """,
            (usuario_id, usuario_id),
        ).fetchall()

        pedidos = {}
        for row in rows:
            pedido = pedidos.get(row["id"])
            if pedido is None:
                pedido = pedidos[row["id"]] = {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
            if row["item_id"] is not None:
                pedido["itens"].append({
                    "produto_id": row["produto_id"],
                    "produto_nome": row["produto_nome"] or PRODUTO_DESCONHECIDO,
                    "quantidade": row["quantidade"],
                    "preco_unitario": row["preco_unitario"],
                })
        return list(pedidos.values())

    def existe(self, pedido_id):
        return self._conn().execute("SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)).fetchone() is not None

    def atualizar_status(self, pedido_id, novo_status):
        conn = self._conn()
        conn.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        conn.commit()

    def resumo_vendas(self):
        row = self._conn().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados,
                   SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()

        total_pedidos = row["total_pedidos"]
        faturamento = row["faturamento"]
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": row["pendentes"] or 0,
            "pedidos_aprovados": row["aprovados"] or 0,
            "pedidos_cancelados": row["cancelados"] or 0,
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }

    def contar(self):
        return self._conn().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
