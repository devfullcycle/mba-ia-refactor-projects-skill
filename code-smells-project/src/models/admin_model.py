"""Operações administrativas sobre o banco."""
import sqlite3

from .database import Database

_TABELAS_RESET = ("itens_pedido", "pedidos", "produtos", "usuarios")


class ConsultaInvalidaError(Exception):
    pass


class AdminModel:
    def __init__(self, db: Database):
        self.db = db

    def resetar(self) -> None:
        conn = self.db.connection()
        with conn:
            for tabela in _TABELAS_RESET:
                conn.execute(f"DELETE FROM {tabela}")  # nomes de tabela são constantes internas

    def consultar_somente_leitura(self, sql: str) -> list:
        """Executa uma única instrução em conexão com PRAGMA query_only (escritas são rejeitadas)."""
        with self.db.read_only_connection() as conn:
            try:
                return [dict(row) for row in conn.execute(sql).fetchall()]
            except (sqlite3.Error, sqlite3.Warning) as erro:
                raise ConsultaInvalidaError(str(erro)) from erro
