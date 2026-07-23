class AppError(Exception):
    status = 500

    def __init__(self, message, status=None):
        super().__init__(message)
        if status is not None:
            self.status = status


class ValidationError(AppError):
    def __init__(self, message):
        super().__init__(message, 400)


class NotFoundError(AppError):
    def __init__(self, message="Recurso nao encontrado"):
        super().__init__(message, 404)


class AuthError(AppError):
    def __init__(self, message="Email ou senha invalidos"):
        super().__init__(message, 401)


class ConflictError(AppError):
    def __init__(self, message):
        super().__init__(message, 409)
