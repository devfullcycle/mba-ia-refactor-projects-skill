import logging

logger = logging.getLogger(__name__)


def notify_order_created(pedido_id, usuario_id):
    logger.info(
        "Notificando criacao do pedido %s para o usuario %s", pedido_id, usuario_id
    )


def notify_order_status(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado - preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado - devolver estoque", pedido_id)
