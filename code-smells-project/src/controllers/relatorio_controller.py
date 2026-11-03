from src.models import pedido_model

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor.
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)


def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0


def relatorio_vendas():
    resumo = pedido_model.resumo_vendas()
    total_pedidos = resumo["total_pedidos"]
    faturamento = resumo["faturamento"]
    desconto = calcular_desconto(faturamento)

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": resumo["pendentes"],
        "pedidos_aprovados": resumo["aprovados"],
        "pedidos_cancelados": resumo["cancelados"],
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
