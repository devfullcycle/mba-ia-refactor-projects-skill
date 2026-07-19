const AppError = require('../errors/AppError');

// Tratamento de erro centralizado — evita try/catch repetido e vazamento de stack trace.
// eslint-disable-next-line no-unused-vars
module.exports = function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
        return res.status(err.statusCode).send(err.message);
    }
    console.error('[ERROR]', err.message);
    res.status(500).send('Erro interno');
};
