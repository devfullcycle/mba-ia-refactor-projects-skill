"""Constantes de domínio (antes espalhadas como literais)."""

APP_VERSION = "1.0.0"

CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]
CATEGORIA_PADRAO = "geral"
NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

TIPO_USUARIO_PADRAO = "cliente"

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_PEDIDO_VALIDOS = [STATUS_PENDENTE, STATUS_APROVADO, STATUS_ENVIADO, STATUS_ENTREGUE, STATUS_CANCELADO]

# (faturamento mínimo exclusivo, taxa de desconto), da maior faixa para a menor
FAIXAS_DESCONTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]
