VALID_CATEGORIES = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]


class ProductModel:
    def __init__(self, db):
        self.db = db

    def find_all(self):
        rows = self.db.execute("SELECT * FROM produtos").fetchall()
        return [self._to_dict(row) for row in rows]

    def find_by_id(self, product_id):
        row = self.db.execute(
            "SELECT * FROM produtos WHERE id = ?", (product_id,)
        ).fetchone()
        return self._to_dict(row) if row else None

    def search(self, termo="", categoria=None, preco_min=None, preco_max=None):
        query = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            query += " AND (nome LIKE ? OR descricao LIKE ?)"
            params.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            query += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            query += " AND preco <= ?"
            params.append(preco_max)
        rows = self.db.execute(query, params).fetchall()
        return [self._to_dict(row) for row in rows]

    def create(self, nome, descricao, preco, estoque, categoria):
        cursor = self.db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        self.db.commit()
        return cursor.lastrowid

    def update(self, product_id, nome, descricao, preco, estoque, categoria):
        self.db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, product_id),
        )
        self.db.commit()

    def delete(self, product_id):
        self.db.execute("DELETE FROM produtos WHERE id = ?", (product_id,))
        self.db.commit()

    def _to_dict(self, row):
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
