class ProdutoModel:
    def __init__(self, banco):
        self._banco = banco

    def listar(self):
        linhas = self._banco.conexao().execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em "
            "FROM produtos ORDER BY id"
        ).fetchall()
        return [dict(linha) for linha in linhas]

    def buscar_por_id(self, produto_id):
        linha = self._banco.conexao().execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em "
            "FROM produtos WHERE id = ?",
            (produto_id,),
        ).fetchone()
        return dict(linha) if linha else None

    def buscar_por_ids(self, produto_ids):
        """Devolve {id: produto} numa única consulta."""
        ids = list(dict.fromkeys(produto_ids))
        marcadores = ", ".join("?" for _ in ids)
        linhas = self._banco.conexao().execute(
            "SELECT id, nome, preco, estoque FROM produtos WHERE id IN (" + marcadores + ")",
            ids,
        ).fetchall()
        return {linha["id"]: dict(linha) for linha in linhas}

    def criar(self, nome, descricao, preco, estoque, categoria):
        conexao = self._banco.conexao()
        with conexao:
            cursor = conexao.execute(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                (nome, descricao, preco, estoque, categoria),
            )
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        conexao = self._banco.conexao()
        with conexao:
            conexao.execute(
                "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? "
                "WHERE id = ?",
                (nome, descricao, preco, estoque, categoria, produto_id),
            )

    def remover(self, produto_id):
        conexao = self._banco.conexao()
        with conexao:
            conexao.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        condicoes = []
        parametros = []
        if termo:
            condicoes.append("(nome LIKE ? OR descricao LIKE ?)")
            parametros += [f"%{termo}%", f"%{termo}%"]
        if categoria:
            condicoes.append("categoria = ?")
            parametros.append(categoria)
        if preco_min is not None:
            condicoes.append("preco >= ?")
            parametros.append(preco_min)
        if preco_max is not None:
            condicoes.append("preco <= ?")
            parametros.append(preco_max)
        filtro = (" WHERE " + " AND ".join(condicoes)) if condicoes else ""
        linhas = self._banco.conexao().execute(
            "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"
            + filtro + " ORDER BY id",
            parametros,
        ).fetchall()
        return [dict(linha) for linha in linhas]
