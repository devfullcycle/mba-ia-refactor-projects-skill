"""Flask routes: input/output adapters only."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import Blueprint, jsonify, request

from store.controllers.orders import OrderController
from store.controllers.products import ProductController
from store.controllers.reports import ReportController
from store.controllers.users import UserController
from store.domain.errors import (
    AuthenticationError,
    AuthorizationError,
    DeprecatedOperationError,
    NotFoundError,
    ValidationError,
)
from store.domain.models import Actor
from store.domain.ports import DatabaseMaintenancePort, TokenPort
from store.views.serializers import public_products, public_user, public_users


def create_blueprint(
    *,
    database: DatabaseMaintenancePort,
    products: ProductController,
    users: UserController,
    orders: OrderController,
    reports: ReportController,
    tokens: TokenPort,
) -> Blueprint:
    api = Blueprint("api", __name__)

    def current_actor() -> Actor:
        header = request.headers.get("Authorization", "")
        scheme, _, value = header.partition(" ")
        if scheme.lower() != "bearer" or not value:
            raise AuthenticationError("Autenticação necessária")
        actor = tokens.verify(value)
        current_user = users.get_for_token(actor.user_id)
        if current_user is None:
            raise AuthenticationError("Token inválido ou expirado")
        return Actor(current_user["id"], current_user["tipo"], current_user["email"])

    def require_auth(handler: Callable):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            return handler(current_actor(), *args, **kwargs)
        return wrapper

    def require_admin(handler: Callable):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            actor = current_actor()
            if not actor.is_admin:
                raise AuthorizationError("Privilégio de administrador necessário")
            return handler(actor, *args, **kwargs)
        return wrapper

    def optional_float(name: str) -> float | None:
        value = request.args.get(name)
        if value in (None, ""):
            return None
        try:
            return float(value)
        except ValueError as exc:
            raise ValidationError(f"{name} inválido") from exc

    @api.get("/")
    def index():
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja", "versao": "1.0.0",
            "endpoints": {
                "produtos": "/produtos", "usuarios": "/usuarios", "pedidos": "/pedidos",
                "login": "/login", "relatorios": "/relatorios/vendas", "health": "/health",
            },
        }), 200

    @api.get("/produtos")
    def list_products():
        return jsonify({"dados": public_products(products.list()), "sucesso": True}), 200

    @api.get("/produtos/busca")
    def search_products():
        result = products.search(
            request.args.get("q", ""), request.args.get("categoria"), optional_float("preco_min"), optional_float("preco_max")
        )
        return jsonify({"dados": public_products(result), "total": len(result), "sucesso": True}), 200

    @api.get("/produtos/<int:product_id>")
    def get_product(product_id: int):
        product = products.get(product_id)
        if product is None:
            raise NotFoundError("Produto não encontrado")
        return jsonify({"dados": product, "sucesso": True}), 200

    @api.post("/produtos")
    @require_admin
    def create_product(_actor: Actor):
        product_id = products.create(request.get_json(silent=True))
        return jsonify({"dados": {"id": product_id}, "sucesso": True, "mensagem": "Produto criado"}), 201

    @api.put("/produtos/<int:product_id>")
    @require_admin
    def update_product(_actor: Actor, product_id: int):
        products.update(product_id, request.get_json(silent=True))
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    @api.delete("/produtos/<int:product_id>")
    @require_admin
    def delete_product(_actor: Actor, product_id: int):
        products.delete(product_id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200

    @api.get("/usuarios")
    @require_admin
    def list_users(_actor: Actor):
        return jsonify({"dados": public_users(users.list()), "sucesso": True}), 200

    @api.get("/usuarios/<int:user_id>")
    @require_auth
    def get_user(actor: Actor, user_id: int):
        if not actor.is_admin and actor.user_id != user_id:
            raise AuthorizationError("Não autorizado para este usuário")
        user = users.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return jsonify({"dados": public_user(user), "sucesso": True}), 200

    @api.post("/usuarios")
    def create_user():
        user_id = users.register(request.get_json(silent=True))
        return jsonify({"dados": {"id": user_id}, "sucesso": True}), 201

    @api.post("/login")
    def login():
        user = users.authenticate(request.get_json(silent=True))
        return jsonify({
            "dados": public_user(user),
            "sucesso": True,
            "mensagem": "Login OK",
            "token": tokens.issue(user),
        }), 200

    @api.post("/pedidos")
    @require_auth
    def create_order(actor: Actor):
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError("Dados inválidos")
        result = orders.create(actor, data.get("usuario_id"), data.get("itens", []))
        return jsonify({"dados": result, "sucesso": True, "mensagem": "Pedido criado com sucesso"}), 201

    @api.get("/pedidos")
    @require_admin
    def list_orders(_actor: Actor):
        return jsonify({"dados": orders.list_all(), "sucesso": True}), 200

    @api.get("/pedidos/usuario/<int:user_id>")
    @require_auth
    def list_user_orders(actor: Actor, user_id: int):
        return jsonify({"dados": orders.list_for_user(actor, user_id), "sucesso": True}), 200

    @api.put("/pedidos/<int:order_id>/status")
    @require_admin
    def update_order_status(_actor: Actor, order_id: int):
        data = request.get_json(silent=True)
        orders.update_status(order_id, data.get("status") if isinstance(data, dict) else None)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    @api.get("/relatorios/vendas")
    @require_admin
    def sales_report(_actor: Actor):
        return jsonify({"dados": reports.sales(), "sucesso": True}), 200

    @api.get("/health")
    def health():
        return jsonify(database.health()), 200

    @api.post("/admin/reset-db")
    @require_admin
    def reset_database(_actor: Actor):
        database.reset()
        return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200

    @api.post("/admin/query")
    @require_admin
    def deprecated_query(_actor: Actor):
        raise DeprecatedOperationError("A execução genérica de SQL foi descontinuada")

    return api
