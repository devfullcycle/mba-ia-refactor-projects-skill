"""Compatibilidade de imports; casos de uso vivem em ``store.controllers``."""

from store.controllers.orders import OrderController
from store.controllers.products import ProductController
from store.controllers.reports import ReportController
from store.controllers.users import UserController

__all__ = [
    "OrderController",
    "ProductController",
    "ReportController",
    "UserController",
]
