from src.config.database import get_db, get_readonly_db


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
    """Executa a consulta em uma conexão somente leitura: escrita é recusada pelo próprio SQLite."""
    conn = get_readonly_db()
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    finally:
        conn.close()
