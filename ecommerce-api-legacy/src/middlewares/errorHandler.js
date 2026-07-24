'use strict';

const { AppError } = require('../utils/errors');

/**
 * Tratamento de erro centralizado. Substitui as respostas em texto puro espalhadas pelos
 * callbacks do legado (e os quatro pontos em que o erro era simplesmente ignorado).
 *
 * Detalhe técnico vai para o log; o cliente recebe mensagem controlada.
 */
function createErrorHandler({ logger }) {
    // A assinatura de 4 argumentos é obrigatória para o Express reconhecer o middleware.
    return function errorHandler(error, req, res, _next) {
        const status = error instanceof AppError ? error.status : 500;
        const expose = error instanceof AppError ? error.expose : false;

        if (status >= 500) {
            logger.error('Erro não tratado', {
                path: req.originalUrl,
                method: req.method,
                message: error.message,
                stack: error.stack,
            });
        } else {
            logger.warn('Requisição rejeitada', {
                path: req.originalUrl,
                method: req.method,
                status,
                message: error.message,
            });
        }

        res.status(status).json({
            error: expose ? error.message : 'Erro interno',
        });
    };
}

function notFoundHandler(req, res) {
    res.status(404).json({ error: `Rota não encontrada: ${req.method} ${req.originalUrl}` });
}

module.exports = { createErrorHandler, notFoundHandler };
