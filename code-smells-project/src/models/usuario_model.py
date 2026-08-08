"""Usuario persistence (parameterized SQL only)."""

from __future__ import annotations

import sqlite3
from typing import Any

from src.models.mappers import usuario_from_row


class UsuarioModel:
    def __init__(self, db: sqlite3.Connection) -> None:
        self._db = db

    def listar_todos(self) -> list[dict[str, Any]]:
        rows = self._db.execute("SELECT * FROM usuarios ORDER BY id").fetchall()
        return [usuario_from_row(row) for row in rows]

    def buscar_por_id(self, usuario_id: int) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return usuario_from_row(row) if row else None

    def buscar_por_email(self, email: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email,),
        ).fetchone()
        return usuario_from_row(row, include_senha=True) if row else None

    def criar(self, nome: str, email: str, senha_hash: str, tipo: str = "cliente") -> int:
        cursor = self._db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, senha_hash, tipo),
        )
        self._db.commit()
        return int(cursor.lastrowid)

    def contar(self) -> int:
        return int(self._db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0])

    @staticmethod
    def para_login(row_dict: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row_dict["id"],
            "nome": row_dict["nome"],
            "email": row_dict["email"],
            "tipo": row_dict["tipo"],
        }
