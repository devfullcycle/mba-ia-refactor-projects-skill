"""Serviço de notificação.

No legado, e-mail/SMS/push eram `print` embutidos no meio do controller de pedidos. Aqui a
integração fica isolada atrás de uma interface: trocar o canal (fila, provedor de e-mail)
não toca em controller nem em model.
"""
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Implementação de desenvolvimento: registra a notificação no log."""

    def __init__(self, canais=("email", "sms", "push")):
        self._canais = tuple(canais)

    def _enviar(self, evento, destinatario, contexto):
        for canal in self._canais:
            logger.info(
                "Notificação enviada", extra={"canal": canal, "evento": evento}
            )
            logger.debug(
                "Detalhe da notificação: canal=%s evento=%s destinatario=%s contexto=%s",
                canal,
                evento,
                destinatario,
                contexto,
            )

    def pedido_criado(self, pedido_id, usuario_id):
        self._enviar(
            "pedido_criado",
            destinatario=usuario_id,
            contexto={"pedido_id": pedido_id},
        )

    def status_alterado(self, pedido_id, novo_status):
        self._enviar(
            "pedido_status_alterado",
            destinatario=None,
            contexto={"pedido_id": pedido_id, "status": novo_status},
        )
