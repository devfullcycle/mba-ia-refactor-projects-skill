from decimal import Decimal

from services.constantes import FAIXAS_DESCONTO
from services.dinheiro import arredondar, para_decimal


def calcular_desconto(faturamento):
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return Decimal("0")


class RelatorioService:
    def __init__(self, pedidos):
        self._pedidos = pedidos

    def vendas(self):
        resumo = self._pedidos.resumo_vendas()
        total_pedidos = resumo["total_pedidos"]
        faturamento = para_decimal(resumo["faturamento"])
        desconto = calcular_desconto(faturamento)
        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": arredondar(faturamento),
            "desconto_aplicavel": arredondar(desconto),
            "faturamento_liquido": arredondar(faturamento - desconto),
            "pedidos_pendentes": resumo["pendentes"],
            "pedidos_aprovados": resumo["aprovados"],
            "pedidos_cancelados": resumo["cancelados"],
            "ticket_medio": arredondar(faturamento / total_pedidos) if total_pedidos > 0 else 0,
        }
