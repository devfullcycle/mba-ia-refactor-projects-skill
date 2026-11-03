// Tratamento de erros centralizado. Mantém o formato texto puro das respostas de erro da API original.
const { AppError } = require('../utils/errors');

function createErrorHandler(logger) {
  // eslint-disable-next-line no-unused-vars
  return function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
      return res.status(err.statusCode).send(err.message);
    }
    if (err.type === 'entity.parse.failed') {
      return res.status(400).send('Bad Request');
    }
    logger.error(`Erro inesperado em ${req.method} ${req.originalUrl}:`, err);
    return res.status(500).send('Erro interno');
  };
}

function notFoundHandler(req, res) {
  res.status(404).send('Rota não encontrada');
}

module.exports = { createErrorHandler, notFoundHandler };
