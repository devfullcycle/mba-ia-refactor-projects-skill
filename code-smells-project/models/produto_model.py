from .database import get_db

class ProdutoModel:
    @staticmethod
    def _format_row(row):
        if not row:
            return None
        return {
            "id": row["id"],
            "nome": row["nome"],
            "descricao": row["descricao"],
            "preco": row["preco"],
            "estoque": row["estoque"],
            "categoria": row["categoria"],
            "ativo": row["ativo"],
            "criado_em": row["criado_em"]
        }

    @classmethod
    def listar_todos(cls):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM produtos WHERE ativo = 1")
        rows = cursor.fetchall()
        return [cls._format_row(row) for row in rows]

    @classmethod
    def buscar_por_id(cls, produto_id):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM produtos WHERE id = ? AND ativo = 1", (produto_id,))
        row = cursor.fetchone()
        return cls._format_row(row)

    @classmethod
    def buscar(cls, termo="", categoria=None, preco_min=None, preco_max=None):
        db = get_db()
        cursor = db.cursor()

        query = "SELECT * FROM produtos WHERE ativo = 1"
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

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [cls._format_row(row) for row in rows]

    @classmethod
    def criar(cls, nome, descricao, preco, estoque, categoria):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO produtos (nome, descricao, preco, estoque, categoria, ativo)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (nome, descricao, preco, estoque, categoria)
        )
        db.commit()
        return cursor.lastrowid

    @classmethod
    def atualizar(cls, produto_id, nome, descricao, preco, estoque, categoria):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            UPDATE produtos
            SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
            WHERE id = ?
            """,
            (nome, descricao, preco, estoque, categoria, produto_id)
        )
        db.commit()
        return cursor.rowcount > 0

    @classmethod
    def deletar(cls, produto_id):
        """Executa exclusão segura preservando integridade referencial."""
        db = get_db()
        cursor = db.cursor()
        # Verificar se existem itens de pedidos vinculados
        cursor.execute("SELECT COUNT(*) FROM itens_pedido WHERE produto_id = ?", (produto_id,))
        if cursor.fetchone()[0] > 0:
            # Soft delete para não quebrar histórico de pedidos
            cursor.execute("UPDATE produtos SET ativo = 0 WHERE id = ?", (produto_id,))
        else:
            cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()
        return True

    @classmethod
    def contar(cls):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM produtos WHERE ativo = 1")
        return cursor.fetchone()[0]
