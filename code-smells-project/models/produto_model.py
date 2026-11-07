class ProdutoModel:
    """Acesso a dados de produtos — queries parametrizadas e serialização única."""

    def __init__(self, conn):
        self._conn = conn

    @staticmethod
    def _serialize(row):
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

    def list(self):
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM produtos")
        return [self._serialize(r) for r in cursor.fetchall()]

    def get(self, produto_id):
        cursor = self._conn.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        row = cursor.fetchone()
        return self._serialize(row) if row else None

    def get_by_ids(self, ids):
        """Busca vários produtos em UMA query (evita N+1)."""
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        cursor = self._conn.cursor()
        cursor.execute(f"SELECT * FROM produtos WHERE id IN ({placeholders})", tuple(ids))
        return {r["id"]: self._serialize(r) for r in cursor.fetchall()}

    def create(self, nome, descricao, preco, estoque, categoria):
        cursor = self._conn.cursor()
        cursor.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        self._conn.commit()
        return cursor.lastrowid

    def update(self, produto_id, nome, descricao, preco, estoque, categoria):
        cursor = self._conn.cursor()
        cursor.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        self._conn.commit()
        return True

    def delete(self, produto_id):
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        self._conn.commit()
        return True

    def search(self, termo, categoria=None, preco_min=None, preco_max=None):
        clauses = ["1=1"]
        params = []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            params.append(preco_max)

        cursor = self._conn.cursor()
        cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clauses)}", tuple(params))
        return [self._serialize(r) for r in cursor.fetchall()]
