from src.models import pedido_model

CASAS_DECIMAIS_MOEDA = 2

# (faturamento mínimo exclusivo, percentual de desconto), da maior faixa para a menor.
FAIXAS_DESCONTO = (
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
)


def _moeda(valor):
    return round(valor, CASAS_DECIMAIS_MOEDA)


def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0


def relatorio_vendas():
    resumo = pedido_model.resumo_vendas()
    faturamento = resumo["faturamento"]
    pedidos_faturados = resumo["pedidos_faturados"]
    desconto = calcular_desconto(faturamento)

    return {
        "total_pedidos": resumo["total_pedidos"],
        "faturamento_bruto": _moeda(faturamento),
        "desconto_aplicavel": _moeda(desconto),
        "faturamento_liquido": _moeda(faturamento - desconto),
        "pedidos_pendentes": resumo["pendentes"],
        "pedidos_aprovados": resumo["aprovados"],
        "pedidos_cancelados": resumo["cancelados"],
        "ticket_medio": _moeda(faturamento / pedidos_faturados) if pedidos_faturados > 0 else 0,
    }
