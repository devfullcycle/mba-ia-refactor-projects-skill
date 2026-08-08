"""Domain exceptions mapped to HTTP by controllers/middleware."""

from __future__ import annotations


class DomainError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class UnauthorizedError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=401)


class ForbiddenError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=403)
