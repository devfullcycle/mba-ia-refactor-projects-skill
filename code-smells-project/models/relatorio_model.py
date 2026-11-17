from .database import get_db
from config.settings import Config

class RelatorioModel:
    @classmethod
    def obter_resumo_vendas(cls):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT COUNT(*) FROM pedidos")
        total_pedidos = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total) FROM pedidos")
        faturamento = cursor.fetchone()[0] or 0.0

        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'pendente'")
        pendentes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'aprovado'")
        aprovados = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = 'cancelado'")
        cancelados = cursor.fetchone()[0]

        # Cálculo do desconto baseado em faixas configuráveis (eliminando números mágicos)
        desconto = 0.0
        for threshold, rate in Config.DISCOUNT_TIERS:
            if faturamento > threshold:
                desconto = faturamento * rate
                break

        faturamento_liquido = faturamento - desconto
        ticket_medio = (faturamento / total_pedidos) if total_pedidos > 0 else 0.0

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento_liquido, 2),
            "pedidos_pendentes": pendentes,
            "pedidos_aprovados": aprovados,
            "pedidos_cancelados": cancelados,
            "ticket_medio": round(ticket_medio, 2)
        }
