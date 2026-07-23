"""Compatibilidade de imports; o adapter SQLite não mantém conexão global."""

from store.infrastructure.sqlite import SQLiteDatabase

__all__ = ["SQLiteDatabase"]
