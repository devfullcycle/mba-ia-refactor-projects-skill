const AppError = require('../errors/AppError');

const INTERNAL_ERROR_MESSAGE = 'Erro interno';

// Mantém o formato original da API: corpo em texto puro com a mensagem. Detalhes internos só vão para o log.
function createErrorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return function errorHandler(err, req, res, next) {
        if (err instanceof AppError) {
            return res.status(err.status).send(err.message);
        }
        if (err && err.type === 'entity.parse.failed') {
            return res.status(400).send('Bad Request');
        }

        logger.error(`Erro inesperado em ${req.method} ${req.originalUrl}`, err);
        res.status(500).send(INTERNAL_ERROR_MESSAGE);
    };
}

module.exports = createErrorHandler;
