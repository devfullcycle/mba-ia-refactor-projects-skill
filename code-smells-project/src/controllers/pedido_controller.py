"""Controller de Pedido — orquestra model, transação e notificação."""
import logging

from src.middlewares.error_handler import NotFoundError
from src.validators.pedido_validator import validate_pedido, validate_status

logger = logging.getLogger(__name__)


class PedidoController:
    def __init__(self, pedido_model, usuario_model, notification_service):
        self._model = pedido_model
        self._usuarios = usuario_model
        self._notifications = notification_service

    def criar(self, dados):
        pedido = validate_pedido(dados)
        if not self._usuarios.exists(pedido["usuario_id"]):
            raise NotFoundError("Usuário não encontrado")

        resultado = self._model.create(pedido["usuario_id"], pedido["itens"])
        logger.info(
            "Pedido criado",
            extra={
                "pedido_id": resultado["pedido_id"],
                "usuario_id": pedido["usuario_id"],
            },
        )
        self._notifications.pedido_criado(
            resultado["pedido_id"], pedido["usuario_id"]
        )
        return {
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }, 201

    def listar_todos(self):
        return {"dados": self._model.list(), "sucesso": True}, 200

    def listar_por_usuario(self, usuario_id):
        return {"dados": self._model.list(usuario_id=usuario_id), "sucesso": True}, 200

    def atualizar_status(self, pedido_id, dados):
        novo_status = validate_status(dados)
        if not self._model.exists(pedido_id):
            raise NotFoundError("Pedido não encontrado")

        self._model.update_status(pedido_id, novo_status)
        logger.info(
            "Status de pedido atualizado",
            extra={"pedido_id": pedido_id, "status": novo_status},
        )
        self._notifications.status_alterado(pedido_id, novo_status)
        return {"sucesso": True, "mensagem": "Status atualizado"}, 200
