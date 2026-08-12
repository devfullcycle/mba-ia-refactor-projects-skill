/**
 * Handler de erros centralizado — converte erros de domínio e internos
 * em respostas JSON padronizadas.
 */
const { CheckoutError } = require('../services/checkoutService');

function notFoundHandler(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

function errorHandler(err, req, res, next) {
    if (err instanceof CheckoutError) {
        return res.status(err.status).json({ error: err.message });
    }
    console.error(err);
    res.status(500).json({ error: 'Erro interno do servidor' });
}

module.exports = { notFoundHandler, errorHandler };