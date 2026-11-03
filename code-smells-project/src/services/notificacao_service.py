"""Notificações de pedido. Hoje apenas registradas em log; ponto único para plugar e-mail/SMS/push."""
import logging

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("Notificação [email/sms/push]: pedido %s criado para usuário %s", pedido_id, usuario_id)


def notificar_mudanca_status(pedido_id, status):
    if status == "aprovado":
        logger.info("Notificação: pedido %s foi aprovado! Preparar envio.", pedido_id)
    elif status == "cancelado":
        logger.info("Notificação: pedido %s cancelado. Devolver estoque.", pedido_id)
