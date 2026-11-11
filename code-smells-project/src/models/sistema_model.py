import sqlite3

from src.config.database import get_db, get_readonly_db

# Colunas que nunca podem ser lidas pela consulta administrativa.
COLUNAS_PROIBIDAS = {("usuarios", "senha")}
ACOES_PERMITIDAS = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


class ConsultaInvalidaError(Exception):
    pass


def _autorizador(acao, arg1, arg2, _db_name, _origem):
    if acao not in ACOES_PERMITIDAS:
        return sqlite3.SQLITE_DENY
    if acao == sqlite3.SQLITE_READ and (arg1, arg2) in COLUNAS_PROIBIDAS:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


def contar_registros():
    row = get_db().execute(
        """
        SELECT (SELECT COUNT(*) FROM produtos) AS produtos,
               (SELECT COUNT(*) FROM usuarios) AS usuarios,
               (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    ).fetchone()
    return dict(row)


def limpar_tabelas():
    db = get_db()
    with db:
        for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
            db.execute(f"DELETE FROM {tabela}")


def executar_consulta_leitura(sql):
    """Conexão somente leitura + authorizer: só SELECT, sem ATTACH/PRAGMA e sem acesso a hashes de senha."""
    conn = get_readonly_db()
    conn.set_authorizer(_autorizador)
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    except sqlite3.Error as exc:
        raise ConsultaInvalidaError(str(exc)) from exc
    finally:
        conn.close()
