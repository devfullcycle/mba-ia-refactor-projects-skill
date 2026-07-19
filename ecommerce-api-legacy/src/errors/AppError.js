// Erro de domínio com código HTTP associado. Controllers repassam via next(err)
// e o middleware central de erro traduz para a resposta HTTP correta.
class AppError extends Error {
    constructor(message, statusCode = 500) {
        super(message);
        this.name = 'AppError';
        this.statusCode = statusCode;
    }
}

module.exports = AppError;
