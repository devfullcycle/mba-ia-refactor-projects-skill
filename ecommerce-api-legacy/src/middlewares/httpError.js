// Erro de domínio com status HTTP associado.
class HttpError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
    }
}

module.exports = HttpError;
