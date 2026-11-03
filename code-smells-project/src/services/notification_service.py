"""Serviço de notificações (e-mail/SMS/push). Hoje apenas registra em log; ponto único para integrar provedores reais."""
import logging


class NotificationService:
    def __init__(self, logger=None):
        self._logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self._logger.info("ENVIANDO EMAIL: Pedido %s criado para usuario %s", pedido_id, usuario_id)
        self._logger.info("ENVIANDO SMS: Seu pedido foi recebido! (pedido %s)", pedido_id)
        self._logger.info("ENVIANDO PUSH: Novo pedido %s recebido pelo sistema", pedido_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            self._logger.info("NOTIFICAÇÃO: Pedido %s foi aprovado! Preparar envio.", pedido_id)
        elif novo_status == "cancelado":
            self._logger.info("NOTIFICAÇÃO: Pedido %s cancelado. Devolver estoque.", pedido_id)
