// Exceções de domínio: convertidas em respostas HTTP pelo middleware de erro.
class AppError extends Error {
  constructor(message, statusCode = 500) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
  }
}

class ValidationError extends AppError {
  constructor(message = 'Bad Request') { super(message, 400); }
}

class UnauthorizedError extends AppError {
  constructor(message = 'Não autorizado') { super(message, 401); }
}

class ForbiddenError extends AppError {
  constructor(message = 'Proibido') { super(message, 403); }
}

class NotFoundError extends AppError {
  constructor(message = 'Não encontrado') { super(message, 404); }
}

class PaymentDeclinedError extends AppError {
  constructor(message = 'Pagamento recusado') { super(message, 400); }
}

module.exports = { AppError, ValidationError, UnauthorizedError, ForbiddenError, NotFoundError, PaymentDeclinedError };
