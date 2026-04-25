from database.connection import get_db
import config.settings as settings


def sales_report():
    db = get_db()

    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento_row = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0]
    faturamento = faturamento_row if faturamento_row else 0

    pendentes = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'").fetchone()[0]
    aprovados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'").fetchone()[0]
    cancelados = db.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'").fetchone()[0]

    desconto = 0
    for threshold, rate in settings.DISCOUNT_TIERS:
        if faturamento > threshold:
            desconto = faturamento * rate
            break

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }


def health_data():
    db = get_db()
    db.execute("SELECT 1")
    produtos = db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
    usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    return {
        "status": "ok",
        "database": "connected",
        "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
    }
