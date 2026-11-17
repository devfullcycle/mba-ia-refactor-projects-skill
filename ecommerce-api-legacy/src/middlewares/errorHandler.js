/**
 * Middleware centralizado de tratamento de erros para Express
 */
function errorHandler(err, req, res, next) {
    console.error(`[ERROR] ${req.method} ${req.url}:`, err);

    if (res.headersSent) {
        return next(err);
    }

    const statusCode = err.status || err.statusCode || 500;
    const isProduction = process.env.NODE_ENV === 'production';

    res.status(statusCode).json({
        error: "Internal Server Error",
        message: isProduction ? "Ocorreu um erro interno no processamento" : (err.message || "Erro inesperado")
    });
}

module.exports = errorHandler;
