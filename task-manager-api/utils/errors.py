"""Exceções de domínio mapeadas para HTTP pelo error handler central."""


class AppError(Exception):
    status = 500

    def __init__(self, message=None):
        super().__init__(message or 'Erro interno')
        self.message = message or 'Erro interno'


class ValidationError(AppError):
    status = 400


class AuthenticationError(AppError):
    status = 401


class ForbiddenError(AppError):
    status = 403


class NotFoundError(AppError):
    status = 404


class ConflictError(AppError):
    status = 409


class DatabaseError(AppError):
    status = 500
