import sqlite3
import threading

from flask import g

ErroBanco = sqlite3.Error


class BancoDados:
    """Uma conexão por contexto de requisição; schema/seed executados uma vez, na primeira conexão."""

    def __init__(self, db_path, inicializador=None):
        self.db_path = db_path
        self._inicializador = inicializador
        self._inicializado = False
        self._trava = threading.Lock()

    def _abrir(self):
        conexao = sqlite3.connect(self.db_path)
        conexao.row_factory = sqlite3.Row
        return conexao

    def _garantir_inicializado(self, conexao):
        if self._inicializado or self._inicializador is None:
            return
        with self._trava:
            if not self._inicializado:
                self._inicializador(conexao)
                self._inicializado = True

    def conexao(self):
        if "db" not in g:
            g.db = self._abrir()
            self._garantir_inicializado(g.db)
        return g.db

    def fechar(self, _erro=None):
        conexao = g.pop("db", None)
        if conexao is not None:
            conexao.close()
