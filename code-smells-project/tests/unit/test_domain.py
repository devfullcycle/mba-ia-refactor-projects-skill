from __future__ import annotations

import unittest

from store.domain.errors import ValidationError
from store.domain.models import OrderItem, ProductData


class ProductDataTests(unittest.TestCase):
    def test_create_and_update_share_the_same_valid_policy(self) -> None:
        raw = {
            "nome": "Produto",
            "descricao": "Descrição",
            "preco": 10,
            "estoque": 2,
            "categoria": "geral",
        }
        first = ProductData.from_mapping(raw)
        second = ProductData.from_mapping(raw)
        self.assertEqual(first, second)

    def test_rejects_invalid_name_category_price_and_stock(self) -> None:
        invalid_cases = (
            {"nome": "x", "preco": 1, "estoque": 1, "categoria": "geral"},
            {"nome": "Produto", "preco": -1, "estoque": 1, "categoria": "geral"},
            {"nome": "Produto", "preco": 1, "estoque": -1, "categoria": "geral"},
            {"nome": "Produto", "preco": 1, "estoque": 1, "categoria": "invalida"},
        )
        for raw in invalid_cases:
            with self.subTest(raw=raw), self.assertRaises(ValidationError):
                ProductData.from_mapping(raw)


class OrderItemTests(unittest.TestCase):
    def test_quantity_must_be_positive(self) -> None:
        for quantity in (0, -1):
            with self.subTest(quantity=quantity), self.assertRaises(ValidationError):
                OrderItem.from_mapping({"produto_id": 1, "quantidade": quantity})
