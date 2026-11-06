from decimal import Decimal

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
STATUS_PEDIDO_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200
PERFIL_ADMIN = "admin"
PERFIL_CLIENTE = "cliente"

# (faturamento acima de, percentual de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = (
    (Decimal("10000"), Decimal("0.10")),
    (Decimal("5000"), Decimal("0.05")),
    (Decimal("1000"), Decimal("0.02")),
)
