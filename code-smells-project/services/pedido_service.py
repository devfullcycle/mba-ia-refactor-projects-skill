"""Regras de negócio do domínio de pedidos (fora de controllers e models)."""

from models import produto_model, pedido_model
from config import settings


class PedidoInvalidoError(Exception):
    """Levantada quando o pedido não respeita as regras de negócio."""


def processar_criacao(usuario_id, itens):
    """Valida itens/estoque e delega a persistência; primeiro item valida tudo.

    Retorna o pedido criado ou levanta PedidoInvalidoError com mensagem legível.
    """
    if not usuario_id:
        raise PedidoInvalidoError("Usuario ID é obrigatório")
    if not itens:
        raise PedidoInvalidoError("Pedido deve ter pelo menos 1 item")

    # Busca os produtos uma única vez (evita N+1).
    ids = [i["produto_id"] for i in itens]
    precos = {}
    for pid in set(ids):
        produto = produto_model.get_produto_por_id(pid)
        if produto is None:
            raise PedidoInvalidoError(f"Produto {pid} não encontrado")
        precos[pid] = produto["preco"]

    # Resolve quantidades e preços unitários
    itens_preparados = []
    for item in itens:
        quantidade = item["quantidade"]
        preco = precos[item["produto_id"]]
        if quantidade and quantidade < 0:
            raise PedidoInvalidoError("Quantidade não pode ser negativa")
        itens_preparados.append(
            {
                "produto_id": item["produto_id"],
                "quantidade": quantidade,
                "preco_unitario": preco,
            }
        )

    resultado = pedido_model.criar_pedido(usuario_id, itens_preparados)
    notificar_pedido_criado(resultado["pedido_id"], usuario_id)
    return resultado


def atualizar_status(pedido_id, novo_status):
    if novo_status not in settings.STATUS_PEDIDO_VALIDOS:
        raise PedidoInvalidoError("Status inválido")
    pedido_model.atualizar_status(pedido_id, novo_status)
    if novo_status == "aprovado":
        log_entrega(pedido_id)
    if novo_status == "cancelado":
        log_restauro_estoque(pedido_id)


def relatorio_vendas_com_desconto():
    """Calcula o relatório aplicando as faixas de desconto da config."""
    base = pedido_model.relatorio_vendas()
    faturamento = base["faturamento_bruto"]
    desconto = 0.0
    for limite, percentual in settings.DESCONTO_FAIXAS:
        if faturamento > limite:
            desconto = faturamento * percentual
            break
    base["desconto_aplicavel"] = round(desconto, 2)
    base["faturamento_liquido"] = round(faturamento - desconto, 2)
    return base


def notificar_pedido_criado(pedido_id, usuario_id):
    # Canal de notificação real (email/sms/push) viria aqui.
    _log(f"Pedido {pedido_id} criado para usuario {usuario_id}")


def log_entrega(pedido_id):
    _log(f"Pedido {pedido_id} aprovado! Preparar envio.")


def log_resto_estoque(pedido_id):
    _log(f"Pedido {pedido_id} cancelado. Devolver estoque.")


def _log(mensagem):
    # Em produção, substituir por logging estruturado.
    import logging

    logging.getLogger("pedido_service").info(mensagem)