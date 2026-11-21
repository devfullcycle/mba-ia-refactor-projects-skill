"""Notificações (simuladas via log; ponto único para trocar por integração real)."""
import logging

from config.constants import STATUS_APROVADO, STATUS_CANCELADO

logger = logging.getLogger(__name__)


def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("ENVIANDO SMS: Seu pedido foi recebido!")
    logger.info("ENVIANDO PUSH: Novo pedido recebido pelo sistema")


def notificar_status_pedido(pedido_id, novo_status):
    if novo_status == STATUS_APROVADO:
        logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
    if novo_status == STATUS_CANCELADO:
        logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
