"""Explicit public DTO presenters."""

from __future__ import annotations


def public_product(product: dict) -> dict:
    return {key: product[key] for key in ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")}


def public_products(products: list[dict]) -> list[dict]:
    return [public_product(product) for product in products]


def public_user(user: dict) -> dict:
    return {
        key: user[key]
        for key in ("id", "nome", "email", "tipo", "criado_em")
        if key in user
    }


def public_users(users: list[dict]) -> list[dict]:
    return [public_user(user) for user in users]


def public_orders(orders: list[dict]) -> list[dict]:
    return orders
