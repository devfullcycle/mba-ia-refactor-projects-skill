'use strict';

/**
 * Erros de domínio. O controller lança; o middleware de erro traduz para HTTP.
 * `expose: true` indica que a mensagem pode ir para o cliente.
 */

class AppError extends Error {
    constructor(message, status = 500, expose = false) {
        super(message);
        this.name = new.target.name;
        this.status = status;
        this.expose = expose;
    }
}

class ValidationError extends AppError {
    constructor(message = 'Bad Request') {
        super(message, 400, true);
    }
}

class NotFoundError extends AppError {
    constructor(message = 'Recurso não encontrado') {
        super(message, 404, true);
    }
}

class UnauthorizedError extends AppError {
    constructor(message = 'Não autorizado') {
        super(message, 401, true);
    }
}

class PaymentDeclinedError extends AppError {
    constructor(message = 'Pagamento recusado') {
        super(message, 400, true);
    }
}

module.exports = {
    AppError,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    PaymentDeclinedError,
};
