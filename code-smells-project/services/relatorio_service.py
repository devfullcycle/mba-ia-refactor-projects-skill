from core.constants import DiscountPolicy
from models import pedido_model  # noqa: F401  (kept for layered symmetry)
from core.db import get_db


def _base_counts():
    db = get_db()
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
    pendentes = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'"
    ).fetchone()[0]
    aprovados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'"
    ).fetchone()[0]
    cancelados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'"
    ).fetchone()[0]
    return total_pedidos, faturamento, pendentes, aprovados, cancelados


def sales_report():
    (
        total_pedidos,
        faturamento,
        pendentes,
        aprovados,
        cancelados,
    ) = _base_counts()

    desconto = faturamento * DiscountPolicy.rate_for(faturamento)

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
