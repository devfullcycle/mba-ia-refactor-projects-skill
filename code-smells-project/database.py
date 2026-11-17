"""Módulo de compatibilidade e facade para a camada models.database."""
from models.database import get_db, close_db, init_db

__all__ = ["get_db", "close_db", "init_db"]
