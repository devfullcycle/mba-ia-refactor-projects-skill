"""Acesso a dados de produtos (consultas parametrizadas)."""

COLUNAS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")
SELECT_PRODUTO = "SELECT " + ", ".join(COLUNAS) + " FROM produtos"


def produto_to_dict(row):
    return {coluna: row[coluna] for coluna in COLUNAS}


class ProdutoModel:
    def __init__(self, get_db):
        self._get_db = get_db

    def listar(self):
        rows = self._get_db().execute(SELECT_PRODUTO).fetchall()
        return [produto_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._get_db().execute(SELECT_PRODUTO + " WHERE id = ?", (produto_id,)).fetchone()
        return produto_to_dict(row) if row else None

    def buscar_por_ids(self, ids):
        """Retorna {id: produto} em uma única consulta."""
        ids = list(set(ids))
        if not ids:
            return {}
        placeholders = ",".join("?" * len(ids))
        rows = self._get_db().execute(SELECT_PRODUTO + " WHERE id IN (" + placeholders + ")", ids).fetchall()
        return {row["id"]: produto_to_dict(row) for row in rows}

    def criar(self, nome, descricao, preco, estoque, categoria):
        db = self._get_db()
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        db.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = self._get_db()
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        db.commit()

    def deletar(self, produto_id):
        db = self._get_db()
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()

    def buscar(self, termo, categoria=None, preco_min=None, preco_max=None):
        query = SELECT_PRODUTO + " WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            like = "%" + termo + "%"
            params += [like, like]
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = self._get_db().execute(query, params).fetchall()
        return [produto_to_dict(row) for row in rows]
