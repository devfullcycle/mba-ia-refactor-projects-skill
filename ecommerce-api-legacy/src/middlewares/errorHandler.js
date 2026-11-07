// Middleware de tratamento de erros centralizado (registrado por último).
// Padroniza as respostas de erro e não vaza stack traces ao cliente.
module.exports = function errorHandler(logger) {
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        const status = err.status || 500;
        if (status >= 500) {
            logger.error(err);
        }
        res.status(status).json({ error: err.message || 'Erro interno' });
    };
};
