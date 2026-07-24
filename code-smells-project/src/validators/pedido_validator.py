"""Validação de Pedido e de transição de status."""
from src.middlewares.error_handler import ValidationError
from src.models.pedido_model import STATUS_VALIDOS


def validate_pedido(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")

    itens = dados.get("itens") or []
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    itens_normalizados = []
    for item in itens:
        if not isinstance(item, dict):
            raise ValidationError("Item inválido")
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not produto_id or not quantidade:
            raise ValidationError("Cada item exige produto_id e quantidade")
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValidationError("Quantidade deve ser um inteiro positivo")
        itens_normalizados.append({"produto_id": produto_id, "quantidade": quantidade})

    return {"usuario_id": usuario_id, "itens": itens_normalizados}


def validate_status(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    novo_status = dados.get("status", "")
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return novo_status
