"""Exceções de domínio mapeadas para respostas HTTP pelo error handler central."""


class AppError(Exception):
    status = 500

    def __init__(self, message, extra=None):
        super().__init__(message)
        self.message = message
        self.extra = extra or {}


class ValidationError(AppError):
    status = 400


class BusinessError(ValidationError):
    """Regra de negócio violada (estoque insuficiente, produto inexistente...)."""

    def __init__(self, message):
        super().__init__(message, {"sucesso": False})


class NotFoundError(AppError):
    status = 404


class UnauthorizedError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403
