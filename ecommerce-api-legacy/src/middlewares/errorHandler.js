const { AppError } = require('../controllers/errors');

// Envelope de erro do legado mantido: texto puro + status code.
function buildErrorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');

        logger.error(`Erro não tratado em ${req.method} ${req.originalUrl}: ${err.stack || err}`);
        return res.status(500).send('Erro interno do servidor');
    };
}

module.exports = { buildErrorHandler };
