"""Adaptador de notificações (e-mail/SMS/push). Hoje apenas registra em log; troque por integrações reais."""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def pedido_criado(self, pedido_id: int, usuario_id: int) -> None:
        logger.info("Notificação [email/sms/push]: pedido %s criado para usuário %s", pedido_id, usuario_id)

    def pedido_aprovado(self, pedido_id: int) -> None:
        logger.info("Notificação: pedido %s aprovado — preparar envio", pedido_id)

    def pedido_cancelado(self, pedido_id: int) -> None:
        logger.info("Notificação: pedido %s cancelado", pedido_id)
