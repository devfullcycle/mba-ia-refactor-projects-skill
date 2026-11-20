"""Agregações de vendas em uma única consulta."""
from .database import Database
from .pedido_model import STATUS_APROVADO, STATUS_CANCELADO, STATUS_PENDENTE


class RelatorioModel:
    def __init__(self, db: Database):
        self.db = db

    def resumo_vendas(self) -> dict:
        row = self.db.connection().execute(
            """
            SELECT COUNT(*)                                   AS total_pedidos,
                   COALESCE(SUM(total), 0)                    AS faturamento,
                   COALESCE(SUM(status = ?), 0)               AS pendentes,
                   COALESCE(SUM(status = ?), 0)               AS aprovados,
                   COALESCE(SUM(status = ?), 0)               AS cancelados
            FROM pedidos
            """,
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()
        return dict(row)
