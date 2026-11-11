const logger = require('../config/logger');
const { AppError } = require('../utils/errors');

function notFoundHandler(req, res) {
    res.status(404).send('Rota não encontrada');
}

// Respostas de erro em texto puro, como no contrato legado. Detalhes internos ficam só no log.
// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
        return res.status(err.statusCode).send(err.message);
    }
    if (err.type === 'entity.parse.failed') {
        return res.status(400).send('Bad Request');
    }
    logger.error('Erro não tratado', { method: req.method, path: req.path, error: err.message, stack: err.stack });
    return res.status(500).send('Erro interno do servidor');
}

module.exports = { errorHandler, notFoundHandler };
