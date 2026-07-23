"""Order and inventory use cases."""

from __future__ import annotations

from store.domain.errors import AuthorizationError, ValidationError
from store.domain.models import Actor, OrderItemInput
from store.domain.ports import OrderRepositoryPort
from store.domain.policies import validate_order_status


class OrderController:
    def __init__(self, repository: OrderRepositoryPort):
        self.repository = repository

    def create(self, actor: Actor, user_id: object, raw_items: object) -> dict:
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            raise ValidationError("Usuario ID é obrigatório")
        if not actor.is_admin and actor.user_id != user_id:
            raise AuthorizationError("Não autorizado para este usuário")
        if not isinstance(raw_items, list) or not raw_items:
            raise ValidationError("Pedido deve ter pelo menos 1 item")
        items = [OrderItemInput.from_mapping(item) for item in raw_items]
        return self.repository.create(user_id, items)

    def list_for_user(self, actor: Actor, user_id: int) -> list[dict]:
        if not actor.is_admin and actor.user_id != user_id:
            raise AuthorizationError("Não autorizado para este usuário")
        return self.repository.list_for_user(user_id)

    def list_all(self) -> list[dict]:
        return self.repository.list_all()

    def update_status(self, order_id: int, raw_status: object) -> None:
        self.repository.update_status(order_id, validate_order_status(raw_status))
