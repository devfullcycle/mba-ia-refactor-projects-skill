"""Sales report queries."""

from __future__ import annotations

import sqlite3
from typing import Any


class RelatorioModel:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def agregados_vendas(self) -> dict[str, Any]:
        total_pedidos = self._db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
        faturamento = self._db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0]
        pendentes = self._db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = ?",
            ("pendente",),
        ).fetchone()[0]
        aprovados = self._db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = ?",
            ("aprovado",),
        ).fetchone()[0]
        cancelados = self._db.execute(
            "SELECT COUNT(*) FROM pedidos WHERE status = ?",
            ("cancelado",),
        ).fetchone()[0]
        return {
            "total_pedidos": total_pedidos,
            "faturamento": float(faturamento or 0),
            "pendentes": pendentes,
            "aprovados": aprovados,
            "cancelados": cancelados,
        }
