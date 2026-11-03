"""Validação de entrada de Pedido."""
from src.models.pedido_model import STATUS_VALIDOS
from src.utils.errors import ValidationError


def _inteiro_positivo(valor):
    return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0


def validar_novo_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    for item in itens:
        if not isinstance(item, dict) or not _inteiro_positivo(item.get("produto_id")) \
                or not _inteiro_positivo(item.get("quantidade")):
            raise ValidationError("Item inválido: produto_id e quantidade (> 0) são obrigatórios")

    return usuario_id, [{"produto_id": i["produto_id"], "quantidade": i["quantidade"]} for i in itens]


def validar_status(dados):
    status = dados.get("status", "") if isinstance(dados, dict) else ""
    if status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return status
