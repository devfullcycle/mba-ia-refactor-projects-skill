class SistemaModel:
    def __init__(self, banco):
        self._banco = banco

    def contagens(self):
        linha = self._banco.conexao().execute(
            "SELECT (SELECT COUNT(*) FROM produtos) AS produtos, "
            "(SELECT COUNT(*) FROM usuarios) AS usuarios, "
            "(SELECT COUNT(*) FROM pedidos) AS pedidos"
        ).fetchone()
        return dict(linha)

    def resetar(self):
        conexao = self._banco.conexao()
        with conexao:
            for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
                conexao.execute("DELETE FROM " + tabela)
