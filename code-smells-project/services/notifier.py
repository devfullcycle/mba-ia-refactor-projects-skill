import logging

logger = logging.getLogger(__name__)


class Notifier:
    """Efeitos colaterais de notificação, isolados do fluxo de negócio.

    Substitui os `print("ENVIANDO EMAIL/SMS/PUSH ...")` espalhados pelo
    controller. Em produção, cada método plugaria um provedor real.
    """

    def pedido_criado(self, usuario_id, pedido_id):
        logger.info("Notificação: pedido %s criado para usuário %s", pedido_id, usuario_id)

    def status_alterado(self, pedido_id, novo_status):
        if novo_status == "aprovado":
            logger.info("Notificação: pedido %s aprovado — preparar envio", pedido_id)
        elif novo_status == "cancelado":
            logger.info("Notificação: pedido %s cancelado — devolver estoque", pedido_id)
