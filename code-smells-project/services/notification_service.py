import logging

logger = logging.getLogger(__name__)


def notify_order_created(pedido_id, usuario_id):
    logger.info("[EMAIL] Pedido %s criado para usuário %s", pedido_id, usuario_id)
    logger.info("[SMS] Confirmação de pedido enviada ao usuário %s", usuario_id)
    logger.info("[PUSH] Novo pedido %s recebido pelo sistema", pedido_id)


def notify_order_status_changed(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("[NOTIFICATION] Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("[NOTIFICATION] Pedido %s cancelado — restaurar estoque", pedido_id)
    else:
        logger.info("[NOTIFICATION] Pedido %s status atualizado para %s", pedido_id, novo_status)
