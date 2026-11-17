from config.constants import STATUS_PEDIDO_VALIDOS
from exceptions import ValidationError


def _eh_inteiro(valor):
    return isinstance(valor, int) and not isinstance(valor, bool)


def validar_pedido(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    if not _eh_inteiro(usuario_id):
        raise ValidationError("Usuario ID inválido")
    if not isinstance(itens, list):
        raise ValidationError("Itens inválidos")
    for item in itens:
        if (
            not isinstance(item, dict)
            or not _eh_inteiro(item.get("produto_id"))
            or not _eh_inteiro(item.get("quantidade"))
            or item["quantidade"] <= 0
        ):
            raise ValidationError("Itens inválidos: informe produto_id e quantidade positiva")

    return usuario_id, itens


def validar_status(dados):
    if not dados or not isinstance(dados, dict):
        raise ValidationError("Dados inválidos")
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
