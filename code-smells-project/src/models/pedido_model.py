"""Model de Pedido — persistência, invariantes e relatório de vendas.

Duas correções estruturais em relação ao legado:
- criação de pedido é atômica (pedido + itens + baixa de estoque em uma transação);
- listagem usa um único JOIN, eliminando o N+1 (era 1 + N + N×M queries).
"""
from src.database.connection import transaction
from src.middlewares.error_handler import BusinessRuleError

STATUS_PENDENTE = "pendente"
STATUS_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")

# Política comercial de desconto sobre o faturamento — antes eram literais soltos.
FAIXAS_DESCONTO = (
    (10_000, 0.10),
    (5_000, 0.05),
    (1_000, 0.02),
)


def calcular_desconto(faturamento):
    for faturamento_minimo, taxa in FAIXAS_DESCONTO:
        if faturamento > faturamento_minimo:
            return faturamento * taxa
    return 0.0


class PedidoModel:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    @property
    def _conn(self):
        return self._connection_provider()

    def create(self, usuario_id, itens):
        """Cria pedido, itens e baixa de estoque em uma única transação."""
        connection = self._conn

        with transaction(connection) as conn:
            itens_calculados = []
            total = 0.0

            for item in itens:
                produto = conn.execute(
                    "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                    (item["produto_id"],),
                ).fetchone()
                if produto is None:
                    raise BusinessRuleError(
                        f"Produto {item['produto_id']} não encontrado"
                    )
                if produto["estoque"] < item["quantidade"]:
                    raise BusinessRuleError(
                        f"Estoque insuficiente para {produto['nome']}"
                    )
                total += produto["preco"] * item["quantidade"]
                itens_calculados.append(
                    {
                        "produto_id": produto["id"],
                        "quantidade": item["quantidade"],
                        "preco_unitario": produto["preco"],
                    }
                )

            cursor = conn.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid

            conn.executemany(
                "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade,"
                " preco_unitario) VALUES (?, ?, ?, ?)",
                [
                    (
                        pedido_id,
                        item["produto_id"],
                        item["quantidade"],
                        item["preco_unitario"],
                    )
                    for item in itens_calculados
                ],
            )

            for item in itens_calculados:
                atualizados = conn.execute(
                    "UPDATE produtos SET estoque = estoque - ?"
                    " WHERE id = ? AND estoque >= ?",
                    (item["quantidade"], item["produto_id"], item["quantidade"]),
                ).rowcount
                if atualizados != 1:
                    # Estoque mudou entre a validação e a baixa: desfaz tudo.
                    raise BusinessRuleError("Estoque insuficiente")

        return {"pedido_id": pedido_id, "total": total}

    def list(self, usuario_id=None):
        """Lista pedidos com seus itens em uma única query (sem N+1)."""
        sql = [
            "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,"
            "       i.produto_id, i.quantidade, i.preco_unitario,"
            "       pr.nome AS produto_nome"
            "  FROM pedidos p"
            "  LEFT JOIN itens_pedido i ON i.pedido_id = p.id"
            "  LEFT JOIN produtos pr    ON pr.id = i.produto_id"
        ]
        parametros = []
        if usuario_id is not None:
            sql.append(" WHERE p.usuario_id = ?")
            parametros.append(usuario_id)
        sql.append(" ORDER BY p.id, i.id")

        rows = self._conn.execute(" ".join(sql), parametros).fetchall()
        return self._agrupar_por_pedido(rows)

    @staticmethod
    def _agrupar_por_pedido(rows):
        pedidos = {}
        ordem = []
        for row in rows:
            pedido_id = row["id"]
            if pedido_id not in pedidos:
                pedidos[pedido_id] = {
                    "id": pedido_id,
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                }
                ordem.append(pedido_id)
            if row["produto_id"] is not None:
                pedidos[pedido_id]["itens"].append(
                    {
                        "produto_id": row["produto_id"],
                        "produto_nome": row["produto_nome"] or "Desconhecido",
                        "quantidade": row["quantidade"],
                        "preco_unitario": row["preco_unitario"],
                    }
                )
        return [pedidos[pedido_id] for pedido_id in ordem]

    def exists(self, pedido_id):
        row = self._conn.execute(
            "SELECT 1 FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        return row is not None

    def update_status(self, pedido_id, novo_status):
        connection = self._conn
        connection.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id)
        )
        connection.commit()

    def sales_report(self):
        """Relatório agregado em duas queries, em vez de cinco COUNT sequenciais."""
        totais = self._conn.execute(
            "SELECT COUNT(*) AS total_pedidos, COALESCE(SUM(total), 0) AS faturamento"
            " FROM pedidos"
        ).fetchone()
        por_status = dict(
            self._conn.execute(
                "SELECT status, COUNT(*) FROM pedidos GROUP BY status"
            ).fetchall()
        )

        total_pedidos = totais["total_pedidos"]
        faturamento = totais["faturamento"] or 0
        desconto = calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": por_status.get("pendente", 0),
            "pedidos_aprovados": por_status.get("aprovado", 0),
            "pedidos_cancelados": por_status.get("cancelado", 0),
            "ticket_medio": (
                round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0
            ),
        }

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
