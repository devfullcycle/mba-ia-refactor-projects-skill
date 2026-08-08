"""Unit tests for report discount rules."""

from __future__ import annotations

from src.services.relatorio_service import RelatorioService


def test_desconto_faixas():
    assert RelatorioService._calcular_desconto(500) == 0.0
    assert RelatorioService._calcular_desconto(1500) == 1500 * 0.02
    assert RelatorioService._calcular_desconto(6000) == 6000 * 0.05
    assert RelatorioService._calcular_desconto(12000) == 12000 * 0.10
