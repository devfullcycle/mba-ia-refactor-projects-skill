"""Serviço de notificações — desacopla os efeitos colaterais (email/sms/push) do controller.

Usa logging estruturado no lugar de `print`. Em produção, plugar aqui os provedores reais.
"""
import logging

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info(
        "Pedido %s criado para usuário %s — disparando email/sms/push", pedido_id, usuario_id
    )


def notificar_status_pedido(pedido_id, status):
    if status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)
