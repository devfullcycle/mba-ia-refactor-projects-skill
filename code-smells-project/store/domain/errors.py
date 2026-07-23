"""Typed errors shared by the domain and application layers."""


class ApplicationError(Exception):
    """Base class for expected failures."""


class ValidationError(ApplicationError):
    pass


class AuthenticationError(ApplicationError):
    pass


class AuthorizationError(ApplicationError):
    pass


class NotFoundError(ApplicationError):
    pass


class ConflictError(ApplicationError):
    pass


class IntegrityError(ApplicationError):
    pass


class DeprecatedOperationError(ApplicationError):
    pass
