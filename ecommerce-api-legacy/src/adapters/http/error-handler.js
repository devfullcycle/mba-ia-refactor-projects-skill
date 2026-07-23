'use strict';

const {
    ValidationError,
    NotFoundError,
    ConflictError,
    PaymentDeniedError,
    AuthenticationError,
    AuthorizationError,
} = require('../../domain/errors');

const STATUS_BY_ERROR = new Map([
    [ValidationError, 400],
    [AuthenticationError, 401],
    [AuthorizationError, 403],
    [NotFoundError, 404],
    [ConflictError, 409],
    [PaymentDeniedError, 400],
]);

/**
 * Handler central de erros (T10/F-010): traduz erro de domínio para
 * contrato HTTP, redige detalhes internos e nunca retorna falso sucesso.
 */
function createErrorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (error, req, res, _next) => {
        if (error && error.type === 'entity.parse.failed' && error.status === 400) {
            return res.status(400).json({ error: 'JSON inválido', code: 'INVALID_JSON' });
        }

        for (const [ErrorType, status] of STATUS_BY_ERROR) {
            if (error instanceof ErrorType) {
                if (status >= 500) {
                    logger.error(error.message, { path: req.path, code: error.code });
                }
                return res.status(status).json({ error: error.message, code: error.code });
            }
        }

        logger.error('Erro não mapeado', { path: req.path, message: error.message });
        return res.status(500).json({ error: 'Erro interno', code: 'INTERNAL_ERROR' });
    };
}

module.exports = { createErrorHandler };
