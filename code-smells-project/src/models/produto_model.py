"""Model de Produto: acesso a dados e regras do domínio de catálogo."""

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"
NOME_MIN_LEN = 2
NOME_MAX_LEN = 200

_CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _to_dict(row):
    return {campo: row[campo] for campo in _CAMPOS}


class ProdutoModel:
    def __init__(self, get_connection):
        self._conn = get_connection

    def listar(self):
        rows = self._conn().execute("SELECT * FROM produtos").fetchall()
        return [_to_dict(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._conn().execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        return _to_dict(row) if row else None

    def buscar_por_ids(self, produto_ids):
        if not produto_ids:
            return {}
        placeholders = ", ".join("?" for _ in produto_ids)
        rows = self._conn().execute(
            f"SELECT * FROM produtos WHERE id IN ({placeholders})", tuple(produto_ids)
        ).fetchall()
        return {row["id"]: _to_dict(row) for row in rows}

    def pesquisar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        clauses, params = [], []
        if termo:
            clauses.append("(nome LIKE ? OR descricao LIKE ?)")
            params += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            clauses.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clauses.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clauses.append("preco <= ?")
            params.append(preco_max)
        where = " AND ".join(clauses) if clauses else "1=1"
        rows = self._conn().execute(f"SELECT * FROM produtos WHERE {where}", params).fetchall()
        return [_to_dict(row) for row in rows]

    def criar(self, nome, descricao, preco, estoque, categoria):
        conn = self._conn()
        cursor = conn.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        conn.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conn = self._conn()
        conn.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        conn.commit()

    def deletar(self, produto_id):
        conn = self._conn()
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conn.commit()

    def baixar_estoque(self, conn, produto_id, quantidade):
        """Decremento condicional (dentro de transação do chamador). Retorna False se faltou estoque."""
        cursor = conn.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
            (quantidade, produto_id, quantidade),
        )
        return cursor.rowcount == 1

    def contar(self):
        return self._conn().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
