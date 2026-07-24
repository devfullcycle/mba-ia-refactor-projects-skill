"""Model de Produto — acesso a dados e invariantes do agregado.

Todas as queries são parametrizadas; a serialização pública tem um único ponto de saída.
"""
from src.middlewares.error_handler import NotFoundError

CAMPOS_PUBLICOS = (
    "id",
    "nome",
    "descricao",
    "preco",
    "estoque",
    "categoria",
    "ativo",
    "criado_em",
)


def _to_dict(row):
    return {campo: row[campo] for campo in CAMPOS_PUBLICOS}


class ProdutoModel:
    def __init__(self, connection_provider):
        self._connection_provider = connection_provider

    @property
    def _conn(self):
        return self._connection_provider()

    def list_all(self):
        rows = self._conn.execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em"
            " FROM produtos ORDER BY id"
        ).fetchall()
        return [_to_dict(row) for row in rows]

    def get(self, produto_id):
        row = self._conn.execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em"
            " FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()
        return _to_dict(row) if row else None

    def get_or_fail(self, produto_id):
        produto = self.get(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado")
        return produto

    def create(self, nome, descricao, preco, estoque, categoria):
        connection = self._conn
        cursor = connection.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
            " VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        connection.commit()
        return cursor.lastrowid

    def update(self, produto_id, nome, descricao, preco, estoque, categoria):
        connection = self._conn
        connection.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?,"
            " categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        connection.commit()

    def delete(self, produto_id):
        connection = self._conn
        connection.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        connection.commit()

    def search(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Filtro dinâmico com fragmentos fixos de SQL — valores sempre parametrizados."""
        clausulas = [
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em"
            " FROM produtos WHERE 1=1"
        ]
        parametros = []

        if termo:
            clausulas.append("AND (nome LIKE ? OR descricao LIKE ?)")
            parametros.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            clausulas.append("AND categoria = ?")
            parametros.append(categoria)
        if preco_min is not None:
            clausulas.append("AND preco >= ?")
            parametros.append(preco_min)
        if preco_max is not None:
            clausulas.append("AND preco <= ?")
            parametros.append(preco_max)

        clausulas.append("ORDER BY id")
        rows = self._conn.execute(" ".join(clausulas), parametros).fetchall()
        return [_to_dict(row) for row in rows]

    def count(self):
        return self._conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
