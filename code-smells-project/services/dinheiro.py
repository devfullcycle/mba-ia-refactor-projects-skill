from decimal import ROUND_HALF_UP, Decimal

CENTAVOS = Decimal("0.01")


def para_decimal(valor):
    return Decimal(str(valor))


def arredondar(valor):
    """Arredonda para 2 casas e devolve float, mantendo o formato numérico das respostas."""
    return float(Decimal(valor).quantize(CENTAVOS, rounding=ROUND_HALF_UP))
