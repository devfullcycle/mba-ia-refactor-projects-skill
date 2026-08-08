"""Pedido persistence with JOIN-based item loading (no N+1)."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.models.mappers import pedido_from_row


class PedidoModel:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def _carregar_pedidos(self, where: str = "", params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        sql = f"SELECT * FROM pedidos {where} ORDER BY id"
        rows = self._db.execute(sql, params).fetchall()
        if not rows:
            return []

        pedidos = {row["id"]: pedido_from_row(row) for row in rows}
        placeholders = ",".join("?" * len(pedidos))
        itens_sql = f"""
            SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario,
                   p.nome AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({placeholders})
            ORDER BY i.id
        """
        item_rows = self._db.execute(itens_sql, tuple(pedidos.keys())).fetchall()
        for item in item_rows:
            pedidos[item["pedido_id"]]["itens"].append(
                {
                    "produto_id": item["produto_id"],
                    "produto_nome": item["produto_nome"] or "Desconhecido",
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                }
            )
        return list(pedidos.values())

    def listar_todos(self) -> list[dict[str, Any]]:
        return self._carregar_pedidos()

    def listar_por_usuario(self, usuario_id: int) -> list[dict[str, Any]]:
        return self._carregar_pedidos("WHERE usuario_id = ?", (usuario_id,))

    def criar(self, usuario_id: int, total: float) -> int:
        cursor = self._db.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
            (usuario_id, total),
        )
        return int(cursor.lastrowid)

    def adicionar_item(
        self,
        pedido_id: int,
        produto_id: int,
        quantidade: int,
        preco_unitario: float,
    ) -> None:
        self._db.execute(
            "INSERT INTO itens_pedido "
            "(pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, produto_id, quantidade, preco_unitario),
        )

    def decrementar_estoque(self, produto_id: int, quantidade: int) -> None:
        self._db.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (quantidade, produto_id),
        )

    def produto_para_pedido(self, produto_id: int) -> sqlite3.Row | None:
        return self._db.execute(
            "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()

    def atualizar_status(self, pedido_id: int, novo_status: str) -> None:
        self._db.execute(
            "UPDATE pedidos SET status = ? WHERE id = ?",
            (novo_status, pedido_id),
        )
        self._db.commit()

    def commit(self) -> None:
        self._db.commit()

    def contar(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0])
