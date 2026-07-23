"""Ports consumed by controllers and external-interface adapters."""

from __future__ import annotations

from typing import Protocol

from .models import Actor, OrderItemInput, ProductInput


class ProductRepositoryPort(Protocol):
    def list_all(self) -> list[dict]: ...

    def get(self, product_id: int) -> dict | None: ...

    def create(self, value: ProductInput) -> int: ...

    def update(self, product_id: int, value: ProductInput) -> None: ...

    def delete(self, product_id: int) -> None: ...

    def search(
        self,
        term: str,
        category: str | None,
        price_min: float | None,
        price_max: float | None,
    ) -> list[dict]: ...


class UserRepositoryPort(Protocol):
    def list_all(self) -> list[dict]: ...

    def get(self, user_id: int) -> dict | None: ...

    def get_by_email(self, email: str) -> dict | None: ...

    def create(
        self,
        name: str,
        email: str,
        password_hash: str,
        role: str = "cliente",
    ) -> int: ...


class OrderRepositoryPort(Protocol):
    def create(self, user_id: int, items: list[OrderItemInput]) -> dict: ...

    def list_for_user(self, user_id: int) -> list[dict]: ...

    def list_all(self) -> list[dict]: ...

    def update_status(self, order_id: int, status: str) -> None: ...

    def report(self) -> dict: ...


class PasswordHasherPort(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, stored_hash: str, password: str) -> bool: ...


class TokenPort(Protocol):
    def issue(self, user: dict) -> str: ...

    def verify(self, token: str) -> Actor: ...


class DatabaseMaintenancePort(Protocol):
    def health(self) -> dict: ...

    def reset(self) -> None: ...
