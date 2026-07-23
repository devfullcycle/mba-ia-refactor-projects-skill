"""Composition root e entry point da API da loja."""

from __future__ import annotations

from flask import Flask, request
from flask_cors import CORS

from config import Settings
from store.controllers.orders import OrderController
from store.controllers.products import ProductController
from store.controllers.reports import ReportController
from store.controllers.users import UserController
from store.infrastructure.repositories import (
    OrderRepository,
    ProductRepository,
    UserRepository,
)
from store.infrastructure.security import PasswordHasher, TokenService
from store.infrastructure.sqlite import SQLiteDatabase
from store.views.error_mapper import register_error_handlers
from store.views.routes import create_blueprint


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    application = Flask(__name__)
    application.config.update(
        SECRET_KEY=settings.secret_key,
        DEBUG=settings.debug,
        ENV=settings.environment,
    )
    CORS(application, origins=settings.cors_origins)

    database = SQLiteDatabase(settings.database_path)
    password_hasher = PasswordHasher()
    token_service = TokenService(settings.secret_key, settings.token_ttl_seconds)

    product_repository = ProductRepository(database)
    user_repository = UserRepository(database)
    order_repository = OrderRepository(database)

    product_controller = ProductController(product_repository)
    user_controller = UserController(user_repository, password_hasher)
    order_controller = OrderController(order_repository)
    report_controller = ReportController(order_repository)
    application.register_blueprint(
        create_blueprint(
            database=database,
            products=product_controller,
            users=user_controller,
            orders=order_controller,
            reports=report_controller,
            tokens=token_service,
        )
    )
    register_error_handlers(application)

    @application.before_request
    def initialize_database() -> None:
        if request.path != "/":
            database.initialize(
                bootstrap_email=settings.bootstrap_admin_email,
                bootstrap_password=settings.bootstrap_admin_password,
            )

    application.extensions["store"] = {
        "database": database,
        "password_hasher": password_hasher,
        "repositories": {
            "products": product_repository,
            "users": user_repository,
            "orders": order_repository,
        },
        "controllers": {
            "products": product_controller,
            "users": user_controller,
            "orders": order_controller,
            "reports": report_controller,
        },
    }
    return application


app = create_app()


if __name__ == "__main__":
    settings = Settings.from_env()
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        use_reloader=settings.debug,
    )
