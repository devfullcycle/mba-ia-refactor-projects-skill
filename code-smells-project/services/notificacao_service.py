import logging

logger = logging.getLogger("app.notificacoes")


class NotificacaoService:
    """Notificações simuladas (e-mail/SMS/push) registradas em log, sem dados pessoais."""

    def pedido_criado(self, pedido_id, usuario_id):
        logger.info("Notificação de pedido criado: pedido_id=%s usuario_id=%s", pedido_id, usuario_id)

    def status_alterado(self, pedido_id, status):
        if status == "aprovado":
            logger.info("Pedido %s aprovado: preparar envio", pedido_id)
        elif status == "cancelado":
            logger.info("Pedido %s cancelado: devolver estoque", pedido_id)
