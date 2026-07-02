const logger = require('../config/logger');

function errorHandler(err, req, res, next) {
    logger.error('Erro não tratado', { error: err.message, path: req.path });
    res.status(500).json({ error: 'Erro interno do servidor' });
}

module.exports = errorHandler;
