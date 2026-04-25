import logging

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def notify_new_order(pedido_id, usuario_id):
        logger.info("Pedido %s criado para usuario %s", pedido_id, usuario_id)

    @staticmethod
    def notify_status_change(pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("Pedido %s aprovado - preparar envio", pedido_id)
        elif novo_status == "cancelado":
            logger.info("Pedido %s cancelado - devolver estoque", pedido_id)
