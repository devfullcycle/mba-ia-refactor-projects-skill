"""Notificações de pedido. Hoje apenas registradas em log; ponto único para plugar e-mail/SMS/push."""
import logging

from src.models.pedido_model import StatusPedido

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação [email/sms/push]: pedido %s criado para usuário %s", pedido_id, usuario_id)


def notificar_mudanca_status(pedido_id, status):
    if status == StatusPedido.APROVADO:
        logger.info("Notificação: pedido %s foi aprovado! Preparar envio.", pedido_id)
    elif status == StatusPedido.CANCELADO:
        logger.info("Notificação: pedido %s cancelado; estoque devolvido.", pedido_id)
