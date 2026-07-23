"""Product use cases."""

from __future__ import annotations

from store.domain.errors import ValidationError
from store.domain.models import ProductInput
from store.domain.ports import ProductRepositoryPort


class ProductController:
    def __init__(self, repository: ProductRepositoryPort):
        self.repository = repository

    def list(self) -> list[dict]:
        return self.repository.list_all()

    def get(self, product_id: int) -> dict | None:
        return self.repository.get(product_id)

    def create(self, data: object) -> int:
        return self.repository.create(ProductInput.from_mapping(data))

    def update(self, product_id: int, data: object) -> None:
        self.repository.update(product_id, ProductInput.from_mapping(data))

    def delete(self, product_id: int) -> None:
        self.repository.delete(product_id)

    def search(
        self,
        term: str,
        category: str | None,
        price_min: float | None,
        price_max: float | None,
    ) -> list[dict]:
        if price_min is not None and price_max is not None and price_min > price_max:
            raise ValidationError("Faixa de preço inválida")
        return self.repository.search(term, category, price_min, price_max)
