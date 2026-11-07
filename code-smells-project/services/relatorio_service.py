class RelatorioService:
    """Monta o relatório de vendas aplicando as faixas de desconto da config."""

    def __init__(self, pedido_model, faixas_desconto):
        self._pedidos = pedido_model
        self._faixas = faixas_desconto

    def _desconto(self, faturamento):
        for minimo, percentual in self._faixas:
            if faturamento > minimo:
                return faturamento * percentual
        return 0

    def vendas(self):
        total, faturamento, por_status = self._pedidos.estatisticas()
        desconto = self._desconto(faturamento)
        return {
            "total_pedidos": total,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": por_status.get("pendente", 0),
            "pedidos_aprovados": por_status.get("aprovado", 0),
            "pedidos_cancelados": por_status.get("cancelado", 0),
            "ticket_medio": round(faturamento / total, 2) if total > 0 else 0,
        }
