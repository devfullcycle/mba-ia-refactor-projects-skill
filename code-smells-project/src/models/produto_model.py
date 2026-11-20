"""Repositório de produtos (queries parametrizadas)."""
from typing import Optional

from .database import Database

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row) -> dict:
    return {campo: row[campo] for campo in _CAMPOS}


class ProdutoModel:
    def __init__(self, db: Database):
        self.db = db

    def listar(self) -> list:
        rows = self.db.connection().execute("SELECT * FROM produtos ORDER BY id").fetchall()
        return [_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id: int) -> Optional[dict]:
        row = self.db.connection().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _to_dict(row) if row else None

    def buscar_por_ids(self, produto_ids) -> dict:
        ids = list(set(produto_ids))
        if not ids:
            return {}
        placeholders = ", ".join("?" for _ in ids)
        rows = self.db.connection().execute(
            f"SELECT * FROM produtos WHERE id IN ({placeholders})", ids  # só placeholders interpolados
        ).fetchall()
        return {row["id"]: _to_dict(row) for row in rows}

    def criar(self, nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> int:
        conn = self.db.connection()
        with conn:
            cursor = conn.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id: int, nome: str, descricao: str, preco: float, estoque: int, categoria: str) -> None:
        conn = self.db.connection()
        with conn:
            conn.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def deletar(self, produto_id: int) -> None:
        conn = self.db.connection()
        with conn:
            conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, termo: str, categoria: Optional[str], preco_min: Optional[float], preco_max: Optional[float]) -> list:
        clausulas, params = ["1=1"], []
        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clausulas.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clausulas.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            params.append(preco_max)
        sql = f"SELECT * FROM produtos WHERE {' AND '.join(clausulas)} ORDER BY id"  # só placeholders interpolados
        rows = self.db.connection().execute(sql, params).fetchall()
        return [_to_dict(row) for row in rows]

    def contar(self) -> int:
        return self.db.connection().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
