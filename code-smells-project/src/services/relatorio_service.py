"""Sales report calculations."""

from __future__ import annotations

from typing import Any

from src.config.settings import DESCONTO_FAIXAS
from src.models.relatorio_model import RelatorioModel


class RelatorioService:
    def __init__(self, model: RelatorioModel) -> None:
        self._model = model

    def vendas(self) -> dict[str, Any]:
        dados = self._model.agregados_vendas()
        faturamento = dados["faturamento"]
        total_pedidos = dados["total_pedidos"]
        desconto = self._calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": dados["pendentes"],
            "pedidos_aprovados": dados["aprovados"],
            "pedidos_cancelados": dados["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }

    @staticmethod
    def _calcular_desconto(faturamento: float) -> float:
        for limite, taxa in DESCONTO_FAIXAS:
            if faturamento > limite:
                return faturamento * taxa
        return 0.0
