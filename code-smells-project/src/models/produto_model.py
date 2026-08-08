"""Produto persistence (parameterized SQL only)."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.models.mappers import produto_from_row


class ProdutoModel:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def listar_todos(self) -> list[dict[str, Any]]:
        rows = self._db.execute("SELECT * FROM produtos ORDER BY id").fetchall()
        return [produto_from_row(row) for row in rows]

    def buscar_por_id(self, produto_id: int) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()
        return produto_from_row(row) if row else None

    def criar(
        self,
        nome: str,
        descricao: str,
        preco: float,
        estoque: int,
        categoria: str,
    ) -> int:
        cursor = self._db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        self._db.commit()
        return int(cursor.lastrowid)

    def atualizar(
        self,
        produto_id: int,
        nome: str,
        descricao: str,
        preco: float,
        estoque: int,
        categoria: str,
    ) -> None:
        self._db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, "
            "estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        self._db.commit()

    def deletar(self, produto_id: int) -> None:
        self._db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        self._db.commit()

    def buscar(
        self,
        termo: str = "",
        categoria: str | None = None,
        preco_min: float | None = None,
        preco_max: float | None = None,
    ) -> list[dict[str, Any]]:
        clauses = ["1=1"]
        params: list[Any] = []

        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            like = f"%{termo}%"
            params.extend([like, like])
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            params.append(preco_max)

        sql = f"SELECT * FROM produtos WHERE {' AND '.join(clauses)} ORDER BY id"
        rows = self._db.execute(sql, params).fetchall()
        return [produto_from_row(row) for row in rows]

    def contar(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0])
