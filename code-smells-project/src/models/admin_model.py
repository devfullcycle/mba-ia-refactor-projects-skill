"""Model de operações administrativas sobre o banco."""

_TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class AdminModel:
    def __init__(self, transaction, get_read_only_connection):
        self._transaction = transaction
        self._get_read_only_connection = get_read_only_connection

    def resetar_dados(self):
        with self._transaction() as conn:
            for tabela in _TABELAS_RESET:  # nomes fixos do código, nunca vindos do request
                conn.execute(f"DELETE FROM {tabela}")

    def consultar_somente_leitura(self, sql):
        """Executa uma única instrução em conexão `mode=ro` (escritas são rejeitadas pelo SQLite)."""
        rows = self._get_read_only_connection().execute(sql).fetchall()
        return [dict(row) for row in rows]
