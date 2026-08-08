"""Shared row → dict mappers (never expose password hashes)."""

from __future__ import annotations

from sqlite3 import Row
from typing import Any


def produto_from_row(row: Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def usuario_from_row(row: Row, *, include_senha: bool = False) -> dict[str, Any]:
    data = {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }
    if include_senha:
        data["senha"] = row["senha"]
    return data


def pedido_from_row(row: Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "usuario_id": row["usuario_id"],
        "status": row["status"],
        "total": row["total"],
        "criado_em": row["criado_em"],
        "itens": [],
    }
