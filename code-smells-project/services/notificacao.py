from utils.logger import get_logger

logger = get_logger(__name__)

def notificar_pedido_criado(pedido_id, usuario_id):
    logger.info(f"Pedido {pedido_id} criado para usuário {usuario_id}")
    logger.info(f"Enviando email de confirmação para usuário {usuario_id}")
    logger.info("Enviando SMS: Seu pedido foi recebido!")
    logger.info("Enviando notificação push: Novo pedido recebido")

def notificar_pedido_aprovado(pedido_id):
    logger.info(f"Pedido {pedido_id} foi aprovado")
    logger.info(f"Iniciando preparação de envio para pedido {pedido_id}")

def notificar_pedido_cancelado(pedido_id):
    logger.info(f"Pedido {pedido_id} cancelado")
    logger.info(f"Devolvendo estoque para pedido {pedido_id}")
