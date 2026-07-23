'use strict';

/**
 * Erros de domínio/aplicação com significado próprio. Tradução para
 * protocolo (status HTTP) acontece somente no error-handler (T10).
 */
class DomainError extends Error {
    constructor(message, code) {
        super(message);
        this.name = new.target.name;
        this.code = code;
    }
}

class ValidationError extends DomainError {
    constructor(message) {
        super(message, 'VALIDATION_ERROR');
    }
}

class NotFoundError extends DomainError {
    constructor(message) {
        super(message, 'NOT_FOUND');
    }
}

class ConflictError extends DomainError {
    constructor(message) {
        super(message, 'CONFLICT');
    }
}

class PaymentDeniedError extends DomainError {
    constructor(message) {
        super(message, 'PAYMENT_DENIED');
    }
}

class AuthenticationError extends DomainError {
    constructor(message) {
        super(message, 'AUTHENTICATION_ERROR');
    }
}

class AuthorizationError extends DomainError {
    constructor(message) {
        super(message, 'AUTHORIZATION_ERROR');
    }
}

module.exports = {
    DomainError,
    ValidationError,
    NotFoundError,
    ConflictError,
    PaymentDeniedError,
    AuthenticationError,
    AuthorizationError,
};
