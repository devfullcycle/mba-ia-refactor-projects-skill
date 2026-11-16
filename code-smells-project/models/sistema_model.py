"""Consultas de infraestrutura: health check e operações administrativas."""
from database import get_db


def contar_registros():
    db = get_db()
    db.execute("SELECT 1")
    return {
        "produtos": db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "usuarios": db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
        "pedidos": db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
    }


def resetar_banco():
    db = get_db()
    for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
        db.execute(f"DELETE FROM {tabela}")
    db.commit()


def executar_sql(sql):
    """Executa SQL arbitrário (somente via rota administrativa autenticada).

    Retorna a lista de linhas para SELECT e None para os demais comandos.
    """
    db = get_db()
    cur = db.execute(sql)
    if sql.strip().upper().startswith("SELECT"):
        return [dict(r) for r in cur.fetchall()]
    db.commit()
    return None
