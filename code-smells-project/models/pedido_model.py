"""Acesso a dados de pedidos e itens (sem N+1)."""
from config.constants import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE

COLUNAS_PEDIDO = ("id", "usuario_id", "status", "total", "criado_em")
SELECT_PEDIDO = "SELECT " + ", ".join(COLUNAS_PEDIDO) + " FROM pedidos"

# Itens de todos os pedidos filtrados, com o nome do produto, em uma única consulta.
SELECT_ITENS = """
    SELECT i.pedido_id, i.produto_id, p.nome AS produto_nome, i.quantidade, i.preco_unitario
    FROM itens_pedido i
    JOIN pedidos pe ON pe.id = i.pedido_id
    LEFT JOIN produtos p ON p.id = i.produto_id
"""

PRODUTO_DESCONHECIDO = "Desconhecido"


class PedidoModel:
    def __init__(self, get_db):
        self._get_db = get_db

    def criar_com_itens(self, usuario_id, linhas, total):
        """Cria o pedido, seus itens e baixa o estoque em uma única transação.

        linhas: [{"produto_id", "quantidade", "preco_unitario"}]
        """
        db = self._get_db()
        try:
            cursor = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid
            for linha in linhas:
                db.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, linha["produto_id"], linha["quantidade"], linha["preco_unitario"]),
                )
                db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (linha["quantidade"], linha["produto_id"]),
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        return pedido_id

    def listar(self, usuario_id=None):
        db = self._get_db()
        filtro = ""
        params = ()
        if usuario_id is not None:
            filtro = " WHERE usuario_id = ?"
            params = (usuario_id,)
        pedidos = [
            {**{coluna: row[coluna] for coluna in COLUNAS_PEDIDO}, "itens": []}
            for row in db.execute(SELECT_PEDIDO + filtro + " ORDER BY id", params).fetchall()
        ]
        if not pedidos:
            return pedidos

        por_id = {pedido["id"]: pedido for pedido in pedidos}
        itens_filtro = " WHERE pe.usuario_id = ?" if usuario_id is not None else ""
        for item in db.execute(SELECT_ITENS + itens_filtro + " ORDER BY i.id", params).fetchall():
            por_id[item["pedido_id"]]["itens"].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"] if item["produto_nome"] is not None else PRODUTO_DESCONHECIDO,
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })
        return pedidos

    def atualizar_status(self, pedido_id, novo_status):
        db = self._get_db()
        db.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
        db.commit()

    def resumo_vendas(self):
        row = self._get_db().execute(
            """
            SELECT COUNT(*) AS total_pedidos,
                   COALESCE(SUM(total), 0) AS faturamento,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,
                   COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return dict(row)
